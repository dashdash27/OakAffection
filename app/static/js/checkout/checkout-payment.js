(() => {
    const checkoutState = window.Checkout.state;
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    
    const errorBox = document.querySelector('.checkout__error-box');
    const errorText = document.querySelector('.checkout__error-text');

    const paymentBtn = document.querySelector('.checkout__payment-btn');
    paymentBtn.addEventListener('click', async (e) => {
        const orderData = {
            "client_total_amount": checkoutState.totalPrice,
            "client_contacts": {
                "name": checkoutState.contacts.name,
                "phone": `${checkoutState.contacts.phone}`,
                "email": checkoutState.contacts.email   
            },
            "delivery": {
                "service": checkoutState.selectedDeliveryOption.service,
                "settlement": {
                    "name": checkoutState.selectedCity.value,
                    "postal_code": checkoutState.selectedCity.postal_code
                },
                "point": {
                    "address": checkoutState.selectedPvz.address,
                    "id": checkoutState.selectedPvz.id
                },
                "days": checkoutState.selectedDeliveryOption.delivery_days,
                "delivery_token": checkoutState.selectedDeliveryOption.delivery_token
            },
            "cart": checkoutState.cart
        }
        console.log("Попытка создания заказа:", orderData);

        // Блокируем paymentBtn
        paymentBtn.disabled = true;
        paymentBtn.textContent = 'Обработка платежа...';

        // Блок с ошибкой очищаем
        errorBox.classList.add("hidden");
        errorText.textContent = '';

        const result = await fetchCreateOrder(orderData);

        // Разблокируем paymentBtn
        resetButton(paymentBtn);

        if (result.success) {
            console.log(`Заказ #${result.data.order_id} успешно создан, переход к оплате`);
            console.log(result.data)

            saveOrderToLS(result.data.order_id, result.data.token);

            window.location.href = result.data.pay_link;
            return;
        } else {
            // TODO: красиво пишет ошибку
            errorBox.classList.remove("hidden");
            errorText.textContent = result.message;
            
            errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });



    async function fetchCreateOrder(orderData) {
        try {
            const response = await fetch(`/checkout/api/orders`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(orderData)
            })

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            }
            
            const errorData = await response.json().catch(() => ({}));

            // Обработка по статус-кодам
            if (response.status === 400) {
                return { 
                    success: false, 
                    message: "Что-то пошло не так. Пожалуйста, попробуйте обновить страницу и оформите заказ снова." 
                };
            }
            if (response.status === 422) {
                if (errorData.error === 'PRICE_MISMATCH') {
                    return { 
                        success: false,
                        message: "Стоимость некоторых товаров изменилась. Пожалуйста, обновите страницу и повторите попытку." 
                    };
                }
                if (errorData.error === 'VALIDATION_ERROR') {
                    return { 
                        success: false,
                        message: "Некоторые данные заполнены некорректно. Пожалуйста, проверьте форму и повторите попытку." 
                    };
                }
                if (errorData.error === 'DELIVERY_ERROR') {
                    return { 
                        success: false,
                        message: "Стоимость доставки могла измениться. Пожалуйста, выберите населенный пункт и детали доставки снова." 
                    };
                }
            }
            if (response.status === 503) {
                return { 
                    success: false, 
                    message: "Платежная система временно недоступна. Пожалуйста, попробуйте оформить заказ еще раз." 
                };
            }
            if (response.status === 500) {
                return { 
                    success: false, 
                    message: "Произошла ошибка на сервере. Мы уже восстанавливаем работу, пожалуйста, попробуйте чуть позже." 
                };
            }
            return { 
            success: false, 
                message: "Не удалось оформить заказ. Пожалуйста, повторите попытку." 
            };
        } catch (error) {
            return { success: false, message: "Проблема с сетью. Пожалуйста, повторите попытку или обновите страницу." };
        }
    }

    function resetButton(button) {
        button.disabled = false;
        button.textContent = 'Перейти к оплате';
    }

    function saveOrderToLS(orderId, token) {
        console.log(`Сохраняем заказ #${orderId} в LS`);
        
        // 1. Сохраняем текущую рабочую корзину в черновик, а оригинал очищаем
        const currentCart = localStorage.getItem('cart');
        localStorage.setItem('cart_draft', currentCart);
        localStorage.removeItem('cart');

        // 2. Зашиваем ID текущего заказа
        localStorage.setItem('current_checkout_order_id', orderId);

        // 3. Сохраняем заказ в локальную историю my_orders
        let myOrders = JSON.parse(localStorage.getItem('my_orders') || '[]');

        const items = JSON.parse(currentCart || '[]'); 

        myOrders.push({
            id: orderId,
            token: token,
            status: 'pending'
        });

        localStorage.setItem('my_orders', JSON.stringify(myOrders));
    }
    
})();