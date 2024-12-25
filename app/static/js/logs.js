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
    
        // Обновленный URL для API
        let url = `/logs/api?offset=${offset}&limit=${limit}`;
        if (userId && userId.trim() !== '') {
            url += `&user_id=${userId}`;
        }
        if (date) {
            url += `&date=${date}`;
        }
        if (searchText && searchText.trim() !== '') {
            url += `&search=${encodeURIComponent(searchText)}`;
        }
    
        if (window.history && window.history.pushState) {
            history.pushState(null, '', `/logs/?offset=${offset}&limit=${limit}`); // Обновляем URL без API
        }
    
        $('#logs-table-body').empty();
    
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
    
                renderPagination();
            },
            error: function (xhr, status, error) {
                console.error('Ошибка при загрузке логов:', error);
            }
        });
    }
    
    
    function renderPagination() {
        const pagination = $('#pagination');
        pagination.empty();
    
        if (totalPages <= 1) return; // Если страниц <= 1, ничего не отображаем
    
        const maxVisiblePages = 3; // Количество страниц вокруг текущей
        let html = '';
    
        // Первая страница
        if (currentPage > 1) {
            html += `<button class="btn btn-sm btn-outline-primary" data-page="1">1</button>`;
        }
    
        // Многоточие перед текущими страницами
        if (currentPage > maxVisiblePages + 1) {
            html += `<span class="btn btn-sm disabled">...</span>`;
        }
    
        // Отображение текущей страницы и двух соседних
        const startPage = Math.max(1, currentPage - maxVisiblePages);
        const endPage = Math.min(totalPages, currentPage + maxVisiblePages);
    
        for (let page = startPage; page <= endPage; page++) {
            const isActive = page === currentPage ? 'active' : '';
            html += `<button class="btn btn-sm btn-outline-primary ${isActive}" data-page="${page}">
                        ${page}
                    </button>`;
        }
    
        // Многоточие после текущих страниц
        if (currentPage < totalPages - maxVisiblePages) {
            html += `<span class="btn btn-sm disabled">...</span>`;
        }
    
        // Последняя страница
        if (currentPage < totalPages) {
            html += `<button class="btn btn-sm btn-outline-primary" data-page="${totalPages}">${totalPages}</button>`;
        }
    
        pagination.html(html);
    
        // Обработчик клика для перехода к нужной странице
        pagination.find('button[data-page]').on('click', function () {
            const selectedPage = parseInt($(this).data('page'));
            if (selectedPage !== currentPage) {
                currentPage = selectedPage;
                offset = (currentPage - 1) * limit;
                savePaginationState();
                loadLogs();
            }
        });
    }
    
    

    setInterval(loadLogs, 60000);

    // Обработка изменения состояния истории (например, при нажатии назад)

    window.onpopstate = function () {
        // Проверяем наличие токена
        const token = localStorage.getItem('access_token');
        if (!token) {
            alert('Токен отсутствует. Пожалуйста, войдите снова.');
            window.location.href = '/login';
            return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const date = urlParams.get('date');
        const searchText = urlParams.get('search');
        const offsetParam = parseInt(urlParams.get('offset'), 10) || 0;
        const limitParam = parseInt(urlParams.get('limit'), 10) || 10;

        if (date) $('#date').val(date);
        if (searchText) $('#search-text').val(searchText);
        offset = offsetParam;
        limit = limitParam;

        // Проверяем токен перед загрузкой логов
        $.ajax({
            url: '/protected',
            type: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token
            },
            success: function () {
                loadLogs(); // Загружаем логи, если токен действителен
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
    };

});
