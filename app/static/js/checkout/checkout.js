(() => {
    // --- UI components
    const checkoutSection = document.querySelector('.checkout');

    const cityInput = document.querySelector('.city-input');
    const citySuggestions = document.querySelector('.city-suggestions');
    const deliveryOptions = document.querySelector('.checkout__delivery-options');
    const deliveryOptionsComment = document.querySelector('.delivery-options-comment');
    const pvzSearchInput = document.querySelector('.pvz-input');
    const pvzComment = document.querySelector('.pvz-comment');
    const pvzSuggestions = document.querySelector('.pvz-suggestions');
    const validationMsg = document.querySelector('.checkout__validation-msg');

    const nameInput = document.querySelector('.name-input');
    const emailInput = document.querySelector('.email-input');
    const phoneInput = document.querySelector('.phone-input');

    const summaryItemsContainer = document.querySelector('.summary__items');
    const summaryItemTemplate = document.querySelector('.summary__item-template');
    const summaryItemDeliveryTemplate = document.querySelector('.summary__item-delivery-template');
    const summaryTotal = document.querySelector('.summary__total-value');
    const summaryTotalComment = document.querySelector('.summary__total-comment');

    const submitBtn = document.querySelector('.checkout__submit-btn');

    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    // --- Config
    const checkoutState = window.Checkout.state;
    const DELIVERY_STYLES = window.Checkout.config.DELIVERY_STYLES;
    const QUANTITY_MAX = window.Checkout.config.QUANTITY_MAX;
    let DISCOUNT_RULES;

    // --- Small Utilities
    let debounceTimer;

    const phoneMask = IMask(phoneInput, {
        mask: '+{7}(000)000-00-00'
    });

    function loadCartFromLS() {
        try {
            const data = localStorage.getItem('cart');
            const cart = data ? JSON.parse(data) : {};
            return (typeof cart === 'object' && cart !== null && !Array.isArray(cart)) ? cart : {};
        }
        catch (e) {
            return {}
        }
    }

    function cleanProductIdsInLS() {
        const rawData = localStorage.getItem('cart');
        const cart = loadCartFromLS();
        let isDirty = false;

        if (rawData && rawData !== '{}' && Object.keys(cart).length === 0) {
            isDirty = true; 
        }

        const cleanCart = {};
        
        for (let id in cart) {
            const count = Number(cart[id]);
            const numericId = Number(id);

            if (!isNaN(numericId) && !isNaN(count) && count > 0 && count <= QUANTITY_MAX) {
                cleanCart[id] = count;
            } else {
                isDirty = true;
            }
        }

        if (isDirty) localStorage.setItem('cart', JSON.stringify(cleanCart));

        return cleanCart
    }

    function getDiscountInfo(amount) {
        const rule = DISCOUNT_RULES.find(current => amount >= current.threshold);
        
        if (rule) {
            const discountAmount = amount * rule.value;
            const finalAmount = Math.ceil(amount - discountAmount);
            
            return { 
                applied: true, 
                label: rule.label, 
                multiplier: rule.value, 
                amount: finalAmount 
            };
        }
        return { 
            applied: false, 
            amount: Math.ceil(amount) 
        };
    }

    function updateTotalPrice() {
        const itemsWithDiscount = Math.ceil(checkoutState.itemsTotal * (1 - checkoutState.discountMultiplier));
        const delivery = checkoutState.selectedDeliveryOption?.price || 0;
        checkoutState.totalPrice = itemsWithDiscount + delivery;
    }


    // --- Step Transitions
    const STEPS_CONFIG = {
        "city-choice": 
            { 
                reset: ['selectedCity', 'deliveryOptions', 'selectedDeliveryOption', 'selectedPvz'], 
                clear: [cityInput, citySuggestions, pvzSearchInput, deliveryOptions, pvzSuggestions],
                messages: [
                    { el: deliveryOptionsComment, text: "Выберите город для расчета доставки" },
                    { el: pvzComment, text: "Выберите службу доставки" }
                ]
            },
        "delivery-choice": 
            { 
                reset: ['deliveryOptions', 'selectedDeliveryOption', 'selectedPvz'], 
                clear: [citySuggestions, deliveryOptionsComment, pvzSearchInput, pvzSuggestions],
                messages: [
                    { el: pvzComment, text: "Выберите службу доставки" }
                ]
            },
        "pvz-choice":
            { 
                reset: ['selectedPvz'], 
                clear: [citySuggestions, deliveryOptionsComment, pvzComment, pvzSearchInput, pvzSuggestions],
                messages: []
            },
        "contacts": 
            { 
                reset: [], 
                clear: [citySuggestions, deliveryOptionsComment, pvzComment, pvzSuggestions],
                messages: []
            },
        "ready": { reset: [], clear: [], messages: [] }
    };

    function changeCheckoutState(state) {
        checkoutSection.dataset.step = state;
        checkoutState.step = state;
        const config = STEPS_CONFIG[state];

        // 1. Reset state variables
        config.reset.forEach(key => checkoutState[key] = null);
        
        // 2. Clear UI elements
        config.clear.forEach(el => { 
            if (el.innerHTML) el.innerHTML = "";
            if (el.value) el.value = "";
        });

        // 3. Set text messages
        if (config.messages) {
            config.messages.forEach(item => {
                if (item.el) item.el.innerHTML = item.text;
            });
        }

        updateTotalPrice();
        renderSummary();

        if (state === "delivery-choice") {
            loadDeliveryOptions(checkoutState.selectedCity);
        }
        if (state === "pvz-choice") {
            renderPvzSuggestions(checkoutState.selectedDeliveryOption.points);
        }
        if (state === "ready") {
            return
        }
        
        validateCheckout();
    }

    // --- API functions
    async function fetchDeliveryOptions(cityData) {
        try {
            const response = await fetch('/checkout/api/delivery/options', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ city_data: cityData, cart: checkoutState.cart })
            })

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            }
            return { success: false, message: "Ошибка сервера при получении вариантов доставок" };
        } catch (error) {
            return { success: false, message: "Проблема с сетью: " + error.message };
        }
    }

    async function loadDeliveryOptions(cityData) {
        const result = await fetchDeliveryOptions(cityData);
        if (result.success) {
            checkoutState.deliveryOptions = result.data["deliveries"];
            renderDeliveryOptions(result.data["deliveries"]);
        } else {
            renderDeliveryOptions({});
            console.log(`Не удалось получить список доступных доставок: ${result.message}`)
        }
    }

    async function fetchCitySuggestions(query) {
        try {
            const response = await fetch(`/checkout/api/suggestions/cities`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ query: query })
            })

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            }
            return { success: false, message: "Ошибка сервера при получении списка городов" };
        } catch (error) {
            return { success: false, message: "Проблема с сетью: " + error.message };
        }
    }

    async function syncCartWithServer(ids) {
        try {
            const response = await fetch('/checkout/api/cart/sync', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ product_ids: ids })
            })

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            }
            return { success: false, message: "Ошибка сервера при загрузке цен" };
        } catch (error) {
            return { success: false, message: "Проблема с сетью: " + error.message };
        }
    }

    function syncLSWithServerIds(serverIds) {
        let cart = loadCartFromLS();
        let changed = false;
        Object.keys(cart).forEach(id => {
            if (!serverIds.includes(String(id))) {
                delete cart[id];
                changed = true;
            }
        });
        if (changed) {
            localStorage.setItem('cart', JSON.stringify(cart));
        }

        return cart
    }


    // --- Event Listeners
    cityInput.addEventListener('input', (e) => {
        checkoutState.selectedCity = null;

        clearTimeout(debounceTimer);
        
        const query = e.target.value.trim();
        if (query.length < 3) {
            return;
        }

        debounceTimer = setTimeout(async () => {
            const result = await fetchCitySuggestions(query);
            if (result.success) {
                checkoutState.currentCitySuggestions = result.data;
                renderCitySuggestions(result.data);
            } else {
                checkoutState.currentCitySuggestions = [];
                console.log(`Не удалось получить список доступных городов: ${result.message}`)
            }
        }, 300);
    });

    cityInput.addEventListener('blur', () => {
        if (!checkoutState.selectedCity) {
            changeCheckoutState("city-choice");
        }
    });

    pvzSearchInput.addEventListener('input', (e) => {
        checkoutState.selectedPvz = null;

        const query = e.target.value.toLowerCase().trim();
        
        const allPoints = checkoutState.selectedDeliveryOption.points;
        const filteredPoints = allPoints.filter(p => 
            p.address.toLowerCase().includes(query)
        );

        renderPvzSuggestions(filteredPoints);
    });

    pvzSearchInput.addEventListener('blur', () => {
        if (!checkoutState.selectedPvz) {
            changeCheckoutState("pvz-choice");
        }
    });

    checkoutSection.addEventListener('mousedown', (e) => {
        const citySuggestion = e.target.closest('.city-suggestion');
        const deliveryCard = e.target.closest('.delivery-card');
        const pvzSuggestion = e.target.closest('.pvz-suggestion');

        if (citySuggestion) {
            checkoutState.selectedCity = checkoutState.currentCitySuggestions[citySuggestion.dataset.index];
            cityInput.value = checkoutState.selectedCity.value;
            changeCheckoutState("delivery-choice");
        }

        if (deliveryCard) {
            if (deliveryCard.classList.contains('delivery-card--disabled')) {
                return; 
            }
            document.querySelectorAll('.delivery-card').forEach(e => {
                e.classList.remove('chosen');
            })
            deliveryCard.classList.add('chosen');
            
            checkoutState.selectedDeliveryOption = checkoutState.deliveryOptions[deliveryCard.dataset.option];
            changeCheckoutState("pvz-choice");
        }

        if (pvzSuggestion) {
            const selectedPvz = checkoutState.selectedDeliveryOption.points.find(p => String(p.id) === String(pvzSuggestion.dataset.id));
            checkoutState.selectedPvz = selectedPvz;
            pvzSearchInput.value = selectedPvz.address;
            changeCheckoutState("contacts");
        }
    });

    nameInput.addEventListener('input', (e) => {
        const value = e.target.value.replace(/[^a-zA-Zа-яА-ЯёЁ\s-]/g, '');
        e.target.value = value;
        checkoutState.contacts.name = value.trim();
        validateCheckout();
    });
    phoneInput.addEventListener('input', () => {
        checkoutState.contacts.phone = phoneMask.unmaskedValue;
        validateCheckout();
    });
    emailInput.addEventListener('input', (e) => {
        checkoutState.contacts.email = e.target.value.trim();
        validateCheckout();
    });


    // --- Render Functions
    function renderCitySuggestions(cities) {
        if (!cities || cities.length === 0) {
            citySuggestions.innerHTML = "";
            return;
        }

        citySuggestions.innerHTML = cities.map((city, index) => {
            return `
                <div class="checkout__suggestion-item city-suggestion" 
                    data-index="${index}">
                    ${city.value}
                </div>
            `;
        }).join('');
    }

    function renderDeliveryOptions(options) {
       if (Object.keys(options).length == 0) {
            deliveryOptionsComment.textContent = "К сожалению, не удалось загрузить службы доставки. Попробуйте снова.";
            deliveryOptions.innerHTML = '';
            return;
        }
        deliveryOptionsComment.textContent = "";
        deliveryOptions.innerHTML = '';

        let hasAnySuccessDelivery = false;

        deliveryOptions.innerHTML = Object.keys(options).map(key => {
            const option = options[key];
            const style = DELIVERY_STYLES[key] || { color: '#ccc', label: '?' };

            if (option.status === "success") {
                hasAnySuccessDelivery = true;
                return `
                    <label class="delivery-card" data-option="${key}">
                        <div class="delivery-card__content">
                            <div class="delivery-card__brand-icon" style="background-color: ${DELIVERY_STYLES[key].color}">
                                ${DELIVERY_STYLES[key].label}
                            </div>
                            <div class="delivery-card__title">${option.name}</div>
                            <div class="delivery-card__additional">
                                <span class="delivery-card__price">${option.price.toLocaleString('ru-RU')} ₽</span>
                                <span class="delivery-card__days">${option.delivery_days}</span>
                            </div>
                        </div>
                    </label>
                `;
            }
            let errorText = "Временно недоступно";
        
            if (option.status === "business_error" && option.error_code === "OVERSIZE_OR_OVERWEIGHT") {
                errorText = "Превышен лимит веса ПВЗ";
            } else if (option.status === "business_error" && option.error_code === "NO_POINTS_IN_REGION") {
                errorText = "Нет пунктов в городе";
            }

            return `
                <div class="delivery-card delivery-card--disabled" data-option="${key}">
                    <div class="delivery-card__content">
                        <div class="delivery-card__brand-icon" style="background-color: #555; color: #aaa;">
                            ${style.label}
                        </div>
                        <div class="delivery-card__title" style="color: #777;">${key === 'yandex' ? 'Яндекс Доставка' : 'Почта России'}</div>
                        <div class="delivery-card__additional">
                            <span class="delivery-card__error-text" style="color: #ff9800; font-size: 13px;">${errorText}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // --- ФИНАЛЬНЫЙ UX ШАГ: Если ВООБЩЕ НИ ОДНА доставка не подошла ---
        if (!hasAnySuccessDelivery) {
            deliveryOptionsComment.innerHTML = `
                <div class="delivery-alert" style="border: 1px solid #ff9800; padding: 15px; border-radius: 8px; margin-top: 15px;">
                    <strong>📦 К сожалению, для этого заказа не нашлось доступных доставок.</strong>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: var(--text-color);">
                        Пожалуйста,
                        <a href="tel:+79604870478" style="color: #4caf50; text-decoration: underline;"><strong>оформите заказ по телефону</strong></a>, 
                        и мы подберем для вас подходящий тип доставки!
                    </p>
                </div>
            `;
        }
    }

    function renderPvzSuggestions(points) {
        if (!points || points.length === 0) {
            pvzSuggestions.innerHTML = 'Ничего не найдено';
            return;
        }

        pvzSuggestions.innerHTML = points.map((point) => {
            return `
                <div class="checkout__suggestion-item pvz-suggestion" data-id="${point.id}">
                    ${point.address}
                </div>
            `;
        }).join('');
    }

    function renderSummary() {
        summaryItemsContainer.innerHTML = "";

        const sortedProducts = [...checkoutState.productsCache].sort((a, b) => Number(a.id) - Number(b.id));
        sortedProducts.forEach(product => {
            const quantity = checkoutState.cart[product.id];
            if (!quantity) return;

            const itemTotal = Number(product.price) * quantity;

            const clone = summaryItemTemplate.content.cloneNode(true);

            clone.querySelector('.summary__item-img').src = product.photo_path;
            clone.querySelector('.summary__item-name').textContent = `${product.name}`;
            clone.querySelector('.summary__item-price').textContent = `${itemTotal.toLocaleString('ru-RU')} ₽`;
            clone.querySelector('.summary__item-qty').textContent = `${quantity} шт`;
            
            summaryItemsContainer.appendChild(clone);
        })

        summaryTotal.innerHTML = `${checkoutState.totalPrice.toLocaleString('ru-RU')} ₽`;

        if (checkoutState.selectedDeliveryOption) {
            const newItem = summaryItemDeliveryTemplate.content.cloneNode(true);
            newItem.querySelector('.summary__item-name').textContent = `Доставка ${checkoutState.selectedDeliveryOption.name}`
            newItem.querySelector('.summary__item-price').textContent = `${checkoutState.selectedDeliveryOption.price.toLocaleString('ru-RU')} ₽`

            summaryItemsContainer.appendChild(newItem);

            summaryTotalComment.innerHTML = ` ${checkoutState.discountLabel ? `Скидка ${checkoutState.discountLabel} на товары применена` : ''}`
        }
        else {
            summaryTotalComment.innerHTML = checkoutState.discountLabel
                    ? `Скидка ${checkoutState.discountLabel} на товары применена. Выберите доставку для финального расчета.` 
                    : 'Выберите доставку для финального расчета'
        }
    }

    // --- Validation
    function validateCheckout() {
        const s = checkoutState;
        const c = checkoutState.contacts;

        let error = "";

        if (!s.selectedCity) {
            error = "Укажите город доставки";
        } else if (!s.selectedDeliveryOption) {
            error = "Выберите способ доставки";
        } else if (s.selectedDeliveryOption.points && !s.selectedPvz) {
            error = "Выберите пункт выдачи из списка";
        } else {
            const nameParts = (c.name || "").trim().split(/\s+/);
            const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c.email || "");

            checkoutSection.dataset.step = "contacts";
            checkoutState.step = "contacts";

            if (nameParts.length < 2 || nameParts[0].length < 2) {
                error = "Введите имя и фамилию для получения заказа";
            } else if ((c.phone || "").length !== 11) {
                error = "Введите корректный номер телефона";
            } else if (!isEmailValid) {
                error = "Проверьте формат почты (например, name@mail.ru)";
            }
            else {
                changeCheckoutState("ready");
            }
        }

        if (validationMsg) {
            validationMsg.textContent = error;
        }

        const isValid = error === "";
        if (submitBtn) {
            submitBtn.disabled = !isValid;
        }
    }

    // --- Initialization
    function initCheckoutState(productsCache, cart) {
        checkoutState.cart = cart;
        checkoutState.productsCache = productsCache;

        let itemsTotal = 0;

        productsCache.forEach(product => {
            const quantity = cart[product.id];
            if (!quantity) return;

            const price = Number(product.price);

            const itemTotal = price * quantity;
            itemsTotal += itemTotal;
        });
        checkoutState.itemsTotal = Number(itemsTotal.toFixed(2));

        const discountInfo = getDiscountInfo(itemsTotal);
        const finalTotal = discountInfo.amount;
        if (discountInfo.applied) {
            checkoutState.discountMultiplier = discountInfo.multiplier;
            checkoutState.discountLabel = discountInfo.label;
        }
        
        checkoutState.totalPrice = finalTotal;
    }

    async function initCheckout() {
        const cart = cleanProductIdsInLS();
        // TODO: редирект если корзина пустая
        
        const ids = Object.keys(cart);
        const result = await syncCartWithServer(ids);

        if (result.success) {
            const productsCache = result.data.products;
            if (result.data.discount_rules && result.data.discount_rules.length > 0) {
                DISCOUNT_RULES = result.data.discount_rules.sort((a, b) => b.threshold - a.threshold);
            }

            const currentCart = syncLSWithServerIds(productsCache.map(p => String(p.id)));
            initCheckoutState(productsCache, currentCart)
            renderSummary(productsCache, currentCart);
        } else {
            console.log(`Не удалось получить данные о товарах в корзине ${result.message}`)
        }
    }

    initCheckout();
})();