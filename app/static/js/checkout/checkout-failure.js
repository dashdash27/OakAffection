document.addEventListener('DOMContentLoaded', async () => {
    // Элементы интерфейса
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    const loader = document.querySelector('.loader');
    const paymentErrorBox = document.querySelector('.payment-error-box');
    const errorBox = document.querySelector('.error-box');

    // Вытаскиваем параметры из адресной строки
    const urlParams = new URLSearchParams(window.location.search);
    const orderId = urlParams.get('order_id');
    const token = urlParams.get('token');

    if (!orderId || !token) {
        loader.classList.add("hidden");
        errorBox.classList.remove("hidden");
        return;
    }

    // Отправляем фетч запрос на сервер
    const result = await fetchOrderStatus(orderId, token);

    loader.classList.add('hidden');

    if (result.success) {
        if (result.data.paid) {
            window.location.href = `success?order_id=${orderId}&token=${token}`;
        }
        else {
            // Восстанавливаем корзину и очищаем временные переменные
            const currentCheckoutId = localStorage.getItem('current_checkout_order_id');
            if (currentCheckoutId && String(currentCheckoutId) === String(orderId)) {
                // Извлекаем черновик корзины
                const cartDraft = localStorage.getItem('cart_draft');
                if (cartDraft) {
                    localStorage.setItem('cart', cartDraft);
                }
                
                // Очищаем за собой временные переменные
                localStorage.removeItem('current_checkout_order_id');
                localStorage.removeItem('cart_draft');
            }

            paymentErrorBox.classList.remove("hidden");
        }
    } else {
        if (result.isInvalidToken) {
            errorBox.classList.remove("hidden");
        }
        else {
            errorBox.classList.remove("hidden");
        }
    }

    
    async function fetchOrderStatus(order_id, token) {
        try {
            const response = await fetch(`/checkout/api/orders/${orderId}/status?token=${token}`, {
                method: 'GET',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })

            if (response.status === 403) {
                return { 
                    success: false, 
                    isInvalidToken: true, 
                    message: "Ссылка недействительна. Обратитесь в техподдержку." 
                };
            }

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            }
            
            const errorData = await response.json().catch(() => ({}));
            return { 
                success: false, 
                message: errorData.error || "Ошибка сервера при запросе статуса заказа" 
            };
        } catch (error) {
            return { success: false, message: "Проблема с сетью: " + error.message };
        }
    }
})