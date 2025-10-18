// Общие функции JavaScript

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Проверка аутентификации при загрузке страниц
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('access_token');
    const currentPath = window.location.pathname;
    
    // Если нет токена и не на странице логина - перенаправляем
    if (!token && currentPath !== '/') {
        window.location.href = '/';
        return;
    }
    
    // Если есть токен и на странице логина - перенаправляем в dashboard
    if (token && currentPath === '/') {
        window.location.href = '/dashboard';
        return;
    }
    
    // Показываем информацию о пользователе
    if (token) {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const userElements = document.querySelectorAll('.user-info');
        userElements.forEach(element => {
            element.textContent = user.full_name || user.email;
        });
    }
});

// Функция для отображения уведомлений
function showNotification(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Добавляем уведомление в начало контента
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(notification, container.firstChild);
    }
    
    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Обработка ошибок API
async function handleApiError(response) {
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
        showNotification(error.detail || 'Произошла ошибка', 'error');
        throw new Error(error.detail);
    }
    return response;
}