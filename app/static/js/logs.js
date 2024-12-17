$(document).ready(function() {
    const token = localStorage.getItem('access_token');
    
    let offset = 0; // Начальный оффсет
    const limit = 10; // Количество записей на странице
    let totalLogs = 0; // Общее количество логов
    let totalPages = 1; // Общее количество страниц
    let currentPage = 1; // Текущая страница

    // Проверка токена
    if (!token) {
        window.location.href = '/login';
    } else {
        $.ajax({
            url: '/protected',
            type: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token
            },
            success: function(response) {
                loadLogs(); // Загружаем логи после проверки токена
            },
            error: function(xhr, status, error) {
                console.error('Ошибка проверки токена:', error);
                window.location.href = '/login';
            }
        });
    }

    $('#fetch-logs').on('click', function() {
        currentPage = 1; // Сбрасываем на первую страницу
        offset = 0; // Сбрасываем оффсет
        loadLogs(); // Загружаем логи
    });
    
    function loadLogs() {
        const userId = $('#user').val(); // Получаем ID пользователя
        const date = $('#date').val(); // Получаем дату
    
        // Формируем URL для запроса
        const url = userId && userId.trim() !== '' ? 
            `/api/logs?user_id=${userId}&date=${date}&offset=${offset}&limit=${limit}` : 
            `/api/logs?date=${date}&offset=${offset}&limit=${limit}`;
    
        $.ajax({
            url: url,
            type: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token
            },
            success: function(response) {
                $('#logs-table-body').empty(); // Очищаем таблицу перед добавлением новых данных
    
                totalLogs = response.total; // Обновляем общее количество логов
                totalPages = Math.ceil(totalLogs / limit); // Расчет общего количества страниц
    
                if (totalLogs === 0) {
                    $('#logs-table-body').append('<tr><td colspan="5">Логи не найдены.</td></tr>');
                } else {
                    response.logs.forEach(function(log) {
                        const row = `<tr>
                                        <td>${log.id}</td>
                                        <td>${log.user_id}</td>
                                        <td>${log.action}</td>
                                        <td>${log.message}</td>
                                        <td>${new Date(log.timestamp).toLocaleString()}</td>
                                    </tr>`;
                        $('#logs-table-body').append(row);
                    });
                }
    
                // Обновляем состояние кнопок пагинации
                $('#prev-page').prop('disabled', currentPage === 1);
                $('#next-page').prop('disabled', currentPage === totalPages);
                $('#page-info').text(`Страница ${currentPage} из ${totalPages}`);
            },
            error: function(xhr, status, error) {
                console.error('Ошибка при загрузке логов:', error);
            }
        });
    }
    

    $('#prev-page').on('click', function() {
        if (currentPage > 1) {
            currentPage--;
            offset = (currentPage - 1) * limit; // Обновляем оффсет
            loadLogs(); // Загружаем логи для предыдущей страницы
        }
    });

    $('#next-page').on('click', function() {
        if (currentPage < totalPages) {
            currentPage++;
            offset = (currentPage - 1) * limit; // Обновляем оффсет
            loadLogs(); // Загружаем логи для следующей страницы
        }
    });

    // Автоматическое обновление данных каждую минуту (по желанию)
    setInterval(loadLogs, 60000);

});
