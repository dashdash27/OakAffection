document.addEventListener('DOMContentLoaded', () => {
    // Находим все кнопки менеджера на странице
    const actionButtons = document.querySelectorAll('.action-btn');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    actionButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            // Извлекаем данные из data-атрибутов кликнутой кнопки
            const orderId = button.getAttribute('data-order-id');
            const action = button.getAttribute('data-action');

            console.log(orderId, action);

            // Вызываем логику обработки (переносим сюда ваш прошлый код)
            if (action === 'refund_mark') {
                if (!confirm("Вы уверены, что хотите отметить заказа как 'Возвращенный'?\nДеньги нужно вернуть руками в ЛК Ozon Pay!")) {
                    return;
                }
            }

            // Вызываем fetch
            const result = await fetchChangeOrderStatus(orderId, action);

            if (result.success) {
                location.reload();
            } else {
                alert(`Ошибка при изменении статуса заказа: ${result.message}`);; 
            }

        });
    });

    async function fetchChangeOrderStatus(orderId, action) {
        try {
            const response = await fetch(`/admin/orders/${orderId}/action`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ action: action })
            })

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            }
            
            const errorData = await response.json().catch(() => ({}));
            return { 
                success: false, 
                message: errorData.error || "Ошибка сервера при изменении статуса заказа" 
            };
        } catch (error) {
            return { success: false, message: "Проблема с сетью: " + error.message };
        }
    }
});