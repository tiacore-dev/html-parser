$(document).ready(function () {
    const token = localStorage.getItem('access_token');
    const urlParams = new URLSearchParams(window.location.search);
    const date = urlParams.get('date');
    const searchText = urlParams.get('search');
    const offsetParam = parseInt(urlParams.get('offset'), 10) || 0;
    const limitParam = parseInt(urlParams.get('limit'), 10) || 10;

    let offset = offsetParam; // Инициализация offset
    let limit = limitParam; // Инициализация limit
    let totalLogs = 0;
    let totalPages = 1;
    let currentPage = parseInt(localStorage.getItem('currentPage')) || 1;

    // Устанавливаем начальные значения в фильтры
    if (date) $('#date').val(date);
    if (searchText) $('#search-text').val(searchText);

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
            success: function () {
                loadLogs();
            },
            error: function (xhr, status, error) {
                if (xhr.status === 401) {
                    alert('Ваша сессия истекла. Пожалуйста, войдите снова.');
                    window.location.href = '/login';
                } else {
                    console.error('Ошибка проверки токена:', error);
                }
            }
        });
    }

    $('#fetch-logs').on('click', function () {
        currentPage = 1;
        offset = 0;
        savePaginationState();
        loadLogs();
    });

    function loadLogs() {
        const userId = $('#user').val();
        const date = $('#date').val();
        const searchText = $('#search-text').val();

        // Формируем URL с параметрами
        let url = `/client/logs?offset=${offset}&limit=${limit}`;
        if (userId && userId.trim() !== '') {
            url += `&user_id=${userId}`;
        }
        if (date) {
            url += `&date=${date}`;
        }
        if (searchText && searchText.trim() !== '') {
            url += `&search=${encodeURIComponent(searchText)}`;
        }

        // Обновляем адресную строку без перезагрузки страницы
        if (window.history && window.history.pushState) {
            history.pushState(null, '', url);
        }

        // Очищаем таблицу перед загрузкой
        $('#logs-table-body').empty();

        // Выполняем запрос к серверу
        $.ajax({
            url: url,
            type: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token
            },
            success: function (response) {
                totalLogs = response.total;
                totalPages = Math.ceil(totalLogs / limit);

                if (totalLogs === 0) {
                    $('#logs-table-body').append('<tr><td colspan="4">Логи не найдены по заданным критериям.</td></tr>');
                } else {
                    response.logs.forEach(function (log) {
                        const escapedMessage = $('<div/>').text(log.message).html();
                        const row = `<tr>
                                        <td>${log.id}</td>
                                        <td>${log.action}</td>
                                        <td>${escapedMessage}</td>
                                        <td>${new Date(log.timestamp).toLocaleString()}</td>
                                    </tr>`;
                        $('#logs-table-body').append(row);
                    });
                }

                $('#prev-page').prop('disabled', currentPage === 1);
                $('#next-page').prop('disabled', currentPage === totalPages);
                $('#page-info').text(`Страница ${currentPage} из ${totalPages}`);
            },
            error: function (xhr, status, error) {
                console.error('Ошибка при загрузке логов:', error);
            }
        });
    }

    function savePaginationState() {
        localStorage.setItem('offset', offset);
        localStorage.setItem('currentPage', currentPage);
    }

    $('#prev-page').on('click', function () {
        if (currentPage > 1) {
            currentPage--;
            offset = (currentPage - 1) * limit;
            savePaginationState();
            loadLogs();
        }
    });

    $('#next-page').on('click', function () {
        if (currentPage < totalPages) {
            currentPage++;
            offset = (currentPage - 1) * limit;
            savePaginationState();
            loadLogs();
        }
    });

    setInterval(loadLogs, 60000);

    // Обработка изменения состояния истории (например, при нажатии назад)
    window.onpopstate = function () {
        const urlParams = new URLSearchParams(window.location.search);
        const date = urlParams.get('date');
        const searchText = urlParams.get('search');
        const offsetParam = parseInt(urlParams.get('offset'), 10) || 0;
        const limitParam = parseInt(urlParams.get('limit'), 10) || 10;

        if (date) $('#date').val(date);
        if (searchText) $('#search-text').val(searchText);
        offset = offsetParam;
        limit = limitParam;

        loadLogs();
    };
});
