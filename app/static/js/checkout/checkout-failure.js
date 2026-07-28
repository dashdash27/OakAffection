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

    console.log(orderId, token);

    // Отправляем фетч запрос на сервер
    const result = await fetchOrderStatus(orderId, token);
    console.log(result.data);

    loader.classList.add('hidden');

    if (result.success) {
        console.log("Токен валидный");

        if (result.data.paid) {
            console.log("Заказ оплачен");

            window.location.href = `success?order_id=${orderId}&token=${token}`;
        }
        else {
            console.log("Заказ не оплачен");

            // Восстанавливаем корзину и очищаем временные переменные
            const currentCheckoutId = localStorage.getItem('current_checkout_order_id');
            if (currentCheckoutId && String(currentCheckoutId) === String(orderId)) {
                console.log(`Текущий ID совпадает с #${orderId}. Восстанавливаем корзину из черновика.`);
                
                // Извлекаем черновик корзины
                const cartDraft = localStorage.getItem('cart_draft');
                if (cartDraft) {
                    localStorage.setItem('cart', cartDraft); 
                    console.log("Корзина успешно восстановлена.");
                }
                
                // Очищаем за собой временные переменные
                localStorage.removeItem('current_checkout_order_id');
                localStorage.removeItem('cart_draft');
            } else {
                console.log("Заказ оформлялся на другом устройстве или сессия устарела");
            }

            paymentErrorBox.classList.remove("hidden");
        }
    } else {
        if (result.isInvalidToken) {
            console.log("Токен не валидный");
            errorBox.classList.remove("hidden");
        }
        else {
            console.log("Ошибка соединения");
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