// --- 1.  Constants and Settings:
const QUANTITY_MAX = 30;
const DISCOUNT_RULES = [
    { threshold: 10000, value: 0.20, label: '20%' },
    { threshold: 30000, value: 0.25, label: '25%' }
].sort((a, b) => a.threshold - b.threshold);

const checkoutState = {
    currentCitySuggestions: [],
    selectedCity: null,
    deliveryOptions: null,
    selectedDeliveryOption: null,
    selectedPvz: null,
    contacts: { name: null, phone: null, email: null }
};

// --- 3. Управление состоянием и UI
const checkoutSection = document.querySelector('.checkout');
const submitBtn = document.querySelector('.checkout__submit-btn');

const cityInput = document.querySelector('.city-input');
const citySuggestions = document.querySelector('.city-suggestions');
const deliveryOptions = document.querySelector('.checkout__delivery-options');
const deliveryOptionsComment = document.querySelector('.delivery-options-comment');
const pvzSearchInput = document.querySelector('.pvz-input');
const pvzComment = document.querySelector('.pvz-comment');
const pvzSuggestions = document.querySelector('.pvz-suggestions');

// Конфиг для сбора данных при переключении шагов
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
};

// Обновление интерфейса при редактировании/сбрасывании данных
function changeCheckoutState(state) {
    checkoutSection.dataset.step = state;
    const config = STEPS_CONFIG[state];

    // 2. Сбрасываем данные в JS-объекте
    config.reset.forEach(key => checkoutState[key] = null);
    
    // 3. Очищаем старые списки (чтобы не было "мерцания")
    config.clear.forEach(el => { 
        if (el.innerHTML) {
            el.innerHTML = ""; 
        }
        if (el.value) {
            el.value = ""
        }
    });

    // 4. Наполняем блоки сообщениями-подсказками
    if (config.messages) {
        config.messages.forEach(item => {
            if (item.el) {
                item.el.innerHTML = item.text;
            }
        });
    }

    if (state === "city-choice") renderSummary(productsCache, syncLSWithServerIds(productsCache.map(p => String(p.id))));
    if (state === "delivery-choice") {
        renderSummary(productsCache, syncLSWithServerIds(productsCache.map(p => String(p.id))))
        loadDeliveryOptions(checkoutState.selectedCity);
    }
    if (state === "pvz-choice") {
        renderSummary(productsCache, syncLSWithServerIds(productsCache.map(p => String(p.id))))
        renderPvzSuggestions(checkoutState.selectedDeliveryOption.points);
    }
    
    validateCheckout();
}

// 2. Утилиты и API
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

function getDiscountInfo(amount) {
    const rule = DISCOUNT_RULES.reduce((acc, current) => amount >= current.threshold ? current : acc, null);
    return rule 
        ? { applied: true, label: rule.label, amount: amount - Math.round(amount * rule.value) }
        : { applied: false, amount };
}

async function fetchDeliveryOptions(cityData) {
    try {
        const response = await fetch('/checkout/api/delivery/options', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ city_data: cityData })
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
        checkoutState.deliveryOptions = result.data;
        renderDeliveryOptions(result.data);
    } else {
        renderDeliveryOptions({});
        console.log(`Не удалось получить список доступных доставок: ${result.message}`)
    }
}

// --- 1 City Step
let debounceTimer;
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

async function fetchCitySuggestions(query) {
    try {
        const response = await fetch(`/checkout/api/suggestions/cities?q=${encodeURIComponent(query)}`, {
            method: 'GET',
            headers: { 
                'Accept': 'application/json'
            }
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

cityInput.addEventListener('blur', () => {
    if (!checkoutState.selectedCity) {
        changeCheckoutState("city-choice");
    }
});

// --- Render
function renderDeliveryOptions(options) {
    if (Object.keys(options).length == 0) {
        deliveryOptionsComment.textContent = "К сожалению, для этого населенного пункта не нашлось доступных доставко. Попробуйте его изменить."
        return
    }
    deliveryOptions.innerHTML = Object.keys(options).map(key => {
        const option = options[key];
        return `
            <label class="delivery-card" data-option="${key}">
                <div class="delivery-card__content">
                    <div class="delivery-card__brand-icon" style="background-color: ${DELIVERY_STYLES[key].color}">
                        ${DELIVERY_STYLES[key].label}
                    </div>
                    <div class="delivery-card__title">${option.name}</div>
                    <div class="delivery-card__additional">
                        <span class="delivery-card__price">${option.price} ₽</span>
                        <span class="delivery-card__days">${option.days}</span>
                    </div>
                </div>
            </label>
        `;
    }).join('');
}

// --- Pvz step
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

// Поиск среди пвз
pvzSearchInput.addEventListener('input', (e) => {
    checkoutState.selectedPvz = null;

    const query = e.target.value.toLowerCase().trim();
    
    // Фильтруем массив из памяти
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

// Contacts inputs
const nameInput = document.querySelector('.name-input');
const emailInput = document.querySelector('.email-input');
const phoneInput = document.querySelector('.phone-input');
const phoneMask = IMask(phoneInput, {
  mask: '+{7}(000)000-00-00'
});

// Обработчики контактов
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

const validationMsg = document.querySelector('.checkout__validation-msg');
// Validate Function
function validateCheckout() {
    const s = checkoutState;
    const c = checkoutState.contacts;

    console.log("Checkout: ", s);
    console.log("Contacts: ", c);

    let error = "";

    if (!s.selectedCity) {
        error = "Укажите город доставки";
    } else if (!s.selectedDeliveryOption) {
        error = "Выберите способ доставки";
    } else if (s.selectedDeliveryOption.points && !s.selectedPvz) {
        error = "Выберите пункт выдачи на карте или из списка";
    } else {
        // Проверка контактов
        const nameParts = (c.name || "").trim().split(/\s+/);
        const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c.email || "");

        if (nameParts.length < 2 || nameParts[0].length < 2) {
            error = "Введите имя и фамилию для получения заказа";
        } else if ((c.phone || "").length !== 11) {
            error = "Введите корректный номер телефона";
        } else if (!isEmailValid) {
            error = "Проверьте формат почты (например, name@mail.ru)";
        }
    }

    // Вывод текста
    if (validationMsg) {
        validationMsg.textContent = error;
    }

    // Состояние кнопки
    const isValid = error === "";
    if (submitBtn) {
        submitBtn.disabled = !isValid;
    }
}

// Helpers:
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

    if (isDirty) {
        localStorage.setItem('cart', JSON.stringify(cleanCart));
    }

    return cleanCart
}

function renderSummary(products, cart) {
    const summaryItemsContainer = document.querySelector('.summary__items');
    const summaryItemTemplate = document.querySelector('.summary__item-template');
    const summaryItemDeliveryTemplate = document.querySelector('.summary__item-delivery-template');
    const summaryTotal = document.querySelector('.summary__total-value');
    const summaryTotalComment = document.querySelector('.summary__total-comment');
    let totalSumm = 0;

    summaryItemsContainer.innerHTML = "";

    const sortedProducts = [...products].sort((a, b) => Number(a.id) - Number(b.id));
    sortedProducts.forEach(product => {
        const quantity = cart[product.id];
        if (!quantity) return;

        const itemTotal = Number(product.price) * quantity;
        totalSumm += itemTotal;

        const clone = summaryItemTemplate.content.cloneNode(true);

        clone.querySelector('.summary__item-img').src = product.photo_path;
        clone.querySelector('.summary__item-name').textContent = `${product.name}`;
        clone.querySelector('.summary__item-price').textContent = `${itemTotal.toLocaleString('ru-RU')} ₽`;
        clone.querySelector('.summary__item-qty').textContent = `${quantity} шт`;
        
        summaryItemsContainer.appendChild(clone);
    })

    // РАсчет скидки и доставки
    const discountInfo = getDiscountInfo(totalSumm);
    const deliveryPrice = checkoutState.selectedDeliveryOption ? Number(checkoutState.selectedDeliveryOption.price) : 0;
    const finalTotal = discountInfo.amount + deliveryPrice;

    summaryTotal.innerHTML = `${finalTotal.toLocaleString('ru-RU')} ₽`;

    if (checkoutState.selectedDeliveryOption) {
        // создаем новый элемент
        const newItem = summaryItemDeliveryTemplate.content.cloneNode(true);
        newItem.querySelector('.summary__item-name').textContent = `Доставка ${checkoutState.selectedDeliveryOption.name}`
        newItem.querySelector('.summary__item-price').textContent = `${deliveryPrice} ₽`

        summaryItemsContainer.appendChild(newItem);


        summaryTotalComment.innerHTML = ` ${discountInfo.applied ? `Скидка ${discountInfo.label} применена` : ''}`
    }
    else {
        summaryTotalComment.innerHTML = discountInfo.applied 
                ? `Скидка ${discountInfo.label} применена. Выберите доставку для финального расчета.` 
                : 'Выберите доставку для финального расчета'
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

let productsCache;
async function initCheckout() {
    const cart = cleanProductIdsInLS();
    // TODO: редирект если корзина пустая
    
    const ids = Object.keys(cart);
    const result = await syncCartWithServer(ids);

    if (result.success) {
        productsCache = result.data;
        const currentCart = syncLSWithServerIds(productsCache.map(p => String(p.id)));
        renderSummary(productsCache, currentCart);
    } else {
        console.log(`Не удалось получить данные о товарах в корзине ${result.message}`)
    }
}

initCheckout();