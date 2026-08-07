document.addEventListener("DOMContentLoaded", function() {
    // Находим все элементы с нашими датами
    document.querySelectorAll('.js-local-time').forEach(function(element) {
        const utcStr = element.getAttribute('data-utc');
        
        if (utcStr) {
            // Создаем объект даты. JS сам поймет, что строка в UTC, 
            // и автоматически переведет её в часовой пояс пользователя.
            const localDate = new Date(utcStr); 
            
            // Проверяем, что дата распарсилась корректно
            if (!isNaN(localDate.getTime())) {
                // Форматируем дату под язык браузера пользователя (дд.мм.гггг, чч:мм)
                element.textContent = localDate.toLocaleString(navigator.language, {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        }
    });
});