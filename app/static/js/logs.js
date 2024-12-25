$(document).ready(function() {
    const token = localStorage.getItem('access_token');
    
    // Начальные значения из localStorage
    let offset = parseInt(localStorage.getItem('offset')) || 0; 
    const limit = 10; 
    let totalLogs = 0; 
    let totalPages = 1; 
    let currentPage = parseInt(localStorage.getItem('currentPage')) || 1;

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
                loadLogs(); 
            },
            error: function(xhr, status, error) {
                console.error('Ошибка проверки токена:', error);
                window.location.href = '/login';
            }
        });
    }

    $('#fetch-logs').on('click', function() {
        currentPage = 1; 
        offset = 0; 
        savePaginationState(); 
        loadLogs(); 
    });

    function loadLogs() {
        const userId = $('#user').val(); 
        const date = $('#date').val(); 
        const searchText = $('#search-text').val(); // Получаем текст поиска
    
        // Формируем URL с параметром поиска
        let url = `/client/logs?offset=${offset}&limit=${limit}`;
        if (userId && userId.trim() !== '') {
            url += `&user_id=${userId}`;
        }
        if (date) {
            url += `&date=${date}`;
        }
        if (searchText && searchText.trim() !== '') {
            url += `&search=${encodeURIComponent(searchText)}`; // Добавляем текст поиска
        }
    
        $.ajax({
            url: url,
            type: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token
            },
            success: function(response) {
                $('#logs-table-body').empty();
    
                totalLogs = response.total; 
                totalPages = Math.ceil(totalLogs / limit);
    
                if (totalLogs === 0) {
                    $('#logs-table-body').append('<tr><td colspan="5">Логи не найдены.</td></tr>');
                } else {
                    response.logs.forEach(function(log) {
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
            error: function(xhr, status, error) {
                console.error('Ошибка при загрузке логов:', error);
            }
        });
    }
    

    function savePaginationState() {
        localStorage.setItem('offset', offset);
        localStorage.setItem('currentPage', currentPage);
    }

    $('#prev-page').on('click', function() {
        if (currentPage > 1) {
            currentPage--;
            offset = (currentPage - 1) * limit; 
            savePaginationState();
            loadLogs(); 
        }
    });

    $('#next-page').on('click', function() {
        if (currentPage < totalPages) {
            currentPage++;
            offset = (currentPage - 1) * limit; 
            savePaginationState();
            loadLogs(); 
        }
    });

    setInterval(loadLogs, 60000);
});
