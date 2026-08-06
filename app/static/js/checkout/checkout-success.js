document.addEventListener('DOMContentLoaded', async () => {
    // Элементы интерфейса
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    const loader = document.querySelector('.loader');
    const successBox = document.querySelector('.success-box');
    const pendingBox = document.querySelector('.pending-box');
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

            // 1. Очищаем current и черновик, если нужно
            const currentCheckoutId = localStorage.getItem('current_checkout_order_id');
            if (currentCheckoutId && String(currentCheckoutId) === String(orderId)) {
                console.log(`Текущий ID совпадает с #${orderId}. Очищаем черновик сессии.`);
                localStorage.removeItem('current_checkout_order_id');
                localStorage.removeItem('cart_draft'); 
            }

            // 2. Если заказ есть в истории, меняем статус и показываем детали. Если нет в истории - детали не показываем
            let myOrders = JSON.parse(localStorage.getItem('my_orders') || '[]');
            const orderIndex = myOrders.findIndex(order => String(order.id) === String(orderId));
            if (orderIndex !== -1) {
                console.log(`Заказ #${orderId} найден в истории. Меняем статус на paid.`);
                myOrders[orderIndex].status = 'paid';
                localStorage.setItem('my_orders', JSON.stringify(myOrders));
                
                renderOrderDetails(result.data.details);
            } else {
                console.log(`Предупреждение: Заказ #${orderId} не найден в локальной истории my_orders.`);

                document.querySelector('.receipt').classList.add('hidden');

                const subMessage = document.querySelector('.sub-message');
                if (subMessage) {
                    subMessage.innerHTML = `Заказ <strong>#${orderId}</strong> оплачен. Детали отправлены на email, указанный при оформлении заказа.`;
                }
            }

            successBox.classList.remove("hidden");
        }
        else {
            console.log("Заказ не оплачен");
            pendingBox.classList.remove("hidden");
        }
    } else {
        if (result.isInvalidToken) {
            console.log("Токен не валидный");
            errorBox.classList.remove("hidden");
        }
        else {
            console.log("Ошибка сервера");
            errorBox.classList.remove("hidden");
        }
    }

    // рендеринг данных в чек
    function renderOrderDetails(details) {
        // 1. Id заказа
        document.querySelector('.order-id').innerHTML = `#${orderId}`;
        
        // 2. Дата и время
        const localDate = new Date(details.created_at);
        const formattedDate = localDate.toLocaleString(navigator.language, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        document.querySelector('.order-date').textContent = formattedDate;

        // 3. Список товаров
        const itemsListContainer = document.querySelector('.receipt__items-list');
        if (details.items && details.items.length > 0) {
            itemsListContainer.innerHTML = details.items.map(item => `
                <div class="receipt__row">
                    <span class="receipt__label receipt__item-name">${item.name}</span>
                    <span class="receipt__label receipt__item-qty">× ${item.quantity}</span>
                    <span class="receipt__value receipt__item-price">${(item.price * item.quantity).toLocaleString('ru-RU')} ₽</span>
                </div>
            `).join('');
        }

        // 4. Delivery
        const orderDelivery = document.querySelector('.order-delivery-service');
        document.querySelector('.order-delivery-price').textContent = `${details.delivery_price.toLocaleString('ru-RU')} ₽`;
        if (details.delivery_service == "russian_post") {
            orderDelivery.textContent = 'Почта России';
            orderDelivery.classList.add('russian-post');
        }
        else if (details.delivery_service == "yandex") {
            orderDelivery.textContent = 'Яндекс';
            orderDelivery.classList.add('yandex');
        }

        // 5. Customer
        if (details.customer) {
            // Форматируем строку: "Иван К. (+7999***1234)"
            document.querySelector('.order-customer').textContent = `${details.customer.name}`;
        }

        // 6. Total
        if (details.total_amount) {
            document.querySelector('.order-total').textContent = `${details.total_amount.toLocaleString('ru-RU')} ₽`;
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