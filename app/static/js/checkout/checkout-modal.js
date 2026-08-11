(() => {
    const checkoutState = window.Checkout.state;

    function generateOrderText() {
        const s = checkoutState;
        const { name, phone, email } = s.contacts;

        // 1. Формируем список товаров 
        const itemsText = s.productsCache
            .filter(p => s.cart[p.id]) 
            .sort((a, b) => a.id - b.id)
            .map(p => `• ${p.name} [${s.cart[p.id]} шт.] — ${(p.price * s.cart[p.id]).toLocaleString('ru-RU')} ₽`)
            .join('\n');

        // 2. Блок итогов и скидки
        const discountNote = s.discountLabel ? ` (применили скидку на товары ${s.discountLabel})` : '';
        const summaryText = `ИТОГО: ${s.totalPrice.toLocaleString('ru-RU')} ₽${discountNote}`;

        // 3. Блок доставки
        const deliveryLine = `• Доставка ${s.selectedDeliveryOption?.name} — ${s.selectedDeliveryOption?.price.toLocaleString('ru-RU')} ₽`;
        const cityLine = `Город/населенный пункт: ${s.selectedCity.value}`;
        const addressLine = `Адрес ПВЗ: ${s.selectedPvz.address}`;

        // 4. Финальная сборка
        const fullText = [
            "НОВЫЙ ЗАКАЗ",
            "----------",
            itemsText,
            deliveryLine,
            "----------",
            summaryText,
            "----------",
            "ДАННЫЕ ПОЛУЧАТЕЛЯ",
            `ФИО: ${name}`,
            `Телефон: ${phone}`,
            `Email: ${email}`,
            cityLine,
            addressLine
        ].join('\n');

        console.log(fullText);
        return fullText;
    }

    const modal = document.querySelector('.order-modal');
    const submitBtn = document.querySelector('.checkout__submit-btn');

    let currentOrderText;

    submitBtn.addEventListener('click', (e) => {
        if (checkoutState.step == "ready") {
            e.preventDefault();

            currentOrderText = generateOrderText();
            const orderReciept = document.querySelector('.order-modal__receipt');
            if (orderReciept) orderReciept.innerText = currentOrderText;
            
            document.body.style.overflow = 'hidden';
            modal.showModal();
        }
    });

    const closeBtn = document.querySelector('.order-modal__close');
    closeBtn.addEventListener('click', () => {
        document.body.style.overflow = '';
        modal.close();
    });

    const copyBtn = document.querySelector('.order-modal__copy');
    let copyTimeout = null; 
    if (copyBtn) {
        const originalBtnText = copyBtn.innerHTML.trim();
        copyBtn.onclick = async () => {
            try {
                await navigator.clipboard.writeText(currentOrderText);
                
                if (copyTimeout) {
                    clearTimeout(copyTimeout);
                }

                copyBtn.innerHTML = "✓ Скопировано!";
                
                copyTimeout = setTimeout(() => {
                    copyBtn.innerHTML = originalBtnText;
                    copyTimeout = null;
                }, 2000);
                
            } catch (err) {
                copyBtn.innerHTML = originalBtnText;
                console.error('Не удалось скопировать:', err);
                alert('Ошибка при копировании. Пожалуйста, выделите текст в чеке вручную.');
            }
        };
    }
})();