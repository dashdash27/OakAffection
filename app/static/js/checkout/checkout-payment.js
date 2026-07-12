(() => {
    const checkoutState = window.Checkout.state;
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    const paymentBtn = document.querySelector('.checkout__payment-btn');
    paymentBtn.addEventListener('click', async (e) => {
        const orderData = {
            "client_total_amount": checkoutState.totalPrice,
            "client_items_total": checkoutState.itemsTotal,
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
                "price": checkoutState.selectedDeliveryOption.price,
                "days": checkoutState.selectedDeliveryOption.delivery_days,
                "delivery_token": checkoutState.selectedDeliveryOption.delivery_token
            },
            "cart": checkoutState.cart
        }
        console.log(orderData);

        const result = await fetchCreateOrder(orderData);
        
        console.log(result);

        if (result.success) {
            console.log("Запрос пришел успешно, переходим на страницу оплаты");
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
    
})();