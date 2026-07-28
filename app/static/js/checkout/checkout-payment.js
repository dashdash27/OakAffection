(() => {
    const checkoutState = window.Checkout.state;
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    const paymentBtn = document.querySelector('.checkout__payment-btn');
    paymentBtn.addEventListener('click', async (e) => {
        const orderData = {
            "client_total_amount": checkoutState.totalPrice,
            "client_contacts": {
                "name": "Иван Иванов",
                "phone": "+78889221122",
                "email": "example@gmail.com"   
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
        console.log(orderData);

        const result = await fetchCreateOrder(orderData);

        if (result.success) {
            console.log(`Заказ #${result.data.order_id} успешно создан, переход к оплате`);
            console.log(result.data)

            saveOrderToLS(result.data.order_id, result.data.token);

            window.location.href = result.data.pay_link;
            return;
        } else {
            alert(result.message); 
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
            return { 
                success: false, 
                message: errorData.error || "Ошибка сервера при создании заказа" 
            };
        } catch (error) {
            return { success: false, message: "Проблема с сетью: " + error.message };
        }
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