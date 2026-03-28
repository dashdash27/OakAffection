const QUANTITY_MAX = 30;
const checkoutState = {
    currentCitySuggestions: [],
    selectedCity: null,
    deliveryOptions: null,
    selectedDeliveryOption: null,
    selectedPvz: null,
    contacts: {
        name: null,
        phone: null,
        email: null
    }
}
// Elements
const checkoutSection = document.querySelector('.checkout');
const cityInput = document.querySelector('.city-input');
const citySuggestions = document.querySelector('.city-suggestions');
const deliveryOptions = document.querySelector('.checkout__delivery-options');
const deliveryOptionsComment = document.querySelector('.delivery-options-comment');
const pvzSearchInput = document.querySelector('.pvz-input');
const pvzComment = document.querySelector('.pvz-comment');
const pvzSuggestions = document.querySelector('.pvz-suggestions');
const submitBtn = document.querySelector('.checkout__submit-btn');

// Обновление интерфейса при редактировании/сбрасывании данных
function changeCheckoutState(state) {
    checkoutSection.dataset.step = state;

    if (state === "city-choice") {
        checkoutState.currentCitySuggestions = [];
        checkoutState.selectedCity = null;
        checkoutState.deliveryOptions = null;
        checkoutState.selectedDeliveryOption = null;
        checkoutState.selectedPvz = null;

        cityInput.value = "";
        citySuggestions.innerHTML = "";
        deliveryOptions.innerHTML = "";
        deliveryOptionsComment.innerHTML = "Варианты доставок появятся после выбора города";
        pvzSearchInput.value = null;
        pvzSearchInput.disabled = true;
        pvzSuggestions.innerHTML = "";
        pvzComment.innerHTML = "Выбрать ПВЗ можно будет после выбора доставки";
    }
    if (state === "delivery-choice") {
        checkoutState.selectedDeliveryOption = null;
        checkoutState.selectedPvz = null;

        citySuggestions.innerHTML = "";
        deliveryOptionsComment.innerHTML = "";
        pvzSearchInput.disabled = true;
        pvzSuggestions.innerHTML = "";
        pvzComment.innerHTML = "Выбрать ПВЗ можно будет после выбора доставки";
    }
    if (state === "pvz-choice") {
        checkoutState.selectedPvz = null;

        deliveryOptionsComment.innerHTML = "";
        pvzSearchInput.disabled = false;
        pvzSearchInput.value = "";
        pvzComment.innerHTML = "";
        renderPvzSuggestions(checkoutState.selectedDeliveryOption.points);
    }
    if (state === "contacts") {
        deliveryOptionsComment.innerHTML = "";
        pvzComment.innerHTML = "";
        pvzSuggestions.innerHTML = "";
    }

    validateCheckout();
}

// --- 1 City Step
let debounceTimer;
cityInput.addEventListener('input', (e) => {
    checkoutState.selectedCity = null;

    clearTimeout(debounceTimer);
    
    const query = e.target.value.trim();
    if (query.length < 3) {
        renderCitySuggestions([]);
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

// --- 2 Delivery Options step
function renderDeliveryOptions() {
    const options = {
        "yandex": {
            "name": "Яндекс Доставка",
            "price": 350,
            "days": "2-3 дня",
            "points": [
                {"id": "y1", "address": "ул. Ленина, 10", "coords": [45.0, 38.9]},
                {"id": "y2", "address": "ул. Мира, 5", "coords": [45.1, 38.8]},
                {"id": "y3", "address": "ул. Покрышкина, 7", "coords": [45.1, 38.8]}
            ]
        },
        "russian_post": {
            "name": "Почта России",
            "price": 280,
            "days": "5-7 дней",
            "points": [
                {"id": "y1", "address": "ул. Цветочная, 10", "coords": [45.0, 38.9]},
                {"id": "y2", "address": "ул. Полевая, 5", "coords": [45.1, 38.8]},
                {"id": "y3", "address": "ул. Покрышкина, 8", "coords": [45.1, 38.8]}
            ]
        }
    }
    checkoutState.deliveryOptions = options;

    deliveryOptions.innerHTML = Object.keys(options).map(key => {
        const option = options[key];
        return `
            <label class="delivery-card" data-option="${key}">
                <div class="delivery-card__content">
                    <span class="delivery-card__title">${option.name}</span>
                    <span class="delivery-card__info">${option.price} ₽ — ${option.days}</span>
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

    pvzSuggestions.innerHTML = points.map((point, index) => {
        return `
            <div class="checkout__suggestion-item pvz-suggestion" 
                 data-id="${point.id}">
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
    if (citySuggestion) {
        const index = parseInt(citySuggestion.dataset.index);
        const cityObject = checkoutState.currentCitySuggestions[index];

        checkoutState.selectedCity = cityObject;

        cityInput.value = checkoutState.selectedCity.value;

        console.log("Список предложений городов:", checkoutState.currentCitySuggestions);
        console.log("Выбранный город:", checkoutState.selectedCity);

        // Переход на следующий этап
        changeCheckoutState("delivery-choice");
        renderDeliveryOptions();
    }

    const deliveryCard = e.target.closest('.delivery-card');
    if (deliveryCard) {
        document.querySelectorAll('.delivery-card').forEach(e => {
            e.classList.remove('chosen');
        })
        deliveryCard.classList.add('chosen');
        
        console.log(deliveryCard.dataset.option);
        checkoutState.selectedDeliveryOption = checkoutState.deliveryOptions[deliveryCard.dataset.option];
        console.log(checkoutState.selectedDeliveryOption);

        // Переход 
        changeCheckoutState("pvz-choice");
    }

    const pvzSuggestion = e.target.closest('.pvz-suggestion');
    if (pvzSuggestion) {
        const index = pvzSuggestion.dataset.id;

        const selectedPvz = checkoutState.selectedDeliveryOption.points.find(point => point.id === index)
        console.log("Выбранный ПВЗ: ", selectedPvz)
        
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
    // Разрешаем только буквы, пробелы и дефис
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

// Validate Function
function validateCheckout() {
    const s = checkoutState;
    const c = checkoutState.contacts;

    console.log("Checkout: ", s);
    console.log("Contacts: ", c);

    const isLocationReady = !!s.selectedCity && !!s.selectedDeliveryOption && !!s.selectedPvz;

    const nameValue = c?.name || "";
    const nameParts = nameValue.trim().split(/\s+/);
    const isNameValid = nameParts.length >= 2 && nameParts[0].length > 0 && nameParts[1].length > 0;

    const phoneValue = c?.phone || "";
    const isPhoneValid = phoneValue.length === 11;

    const emailValue = c?.email || "";
    const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue);

    const isValid = isLocationReady && isNameValid && isPhoneValid && isEmailValid;

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
    // return cleanCart
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
        console.log("Корзина была очищена от некорректных данных");
    }

    return cleanCart
}

function renderSummary(products, cart) {
    const summaryItemsContainer = document.querySelector('.summary__items');
    const summaryItemTemplate = document.querySelector('.summary__item-template');

    summaryItemsContainer.innerHTML = "";

    const sortedProducts = [...products].sort((a, b) => Number(a.id) - Number(b.id));
    sortedProducts.forEach(product => {
        const clone = summaryItemTemplate.content.cloneNode(true);
        const summaryItem = clone.querySelector('.summary__item');

        if (!cart[product.id]) return;

        summaryItem.querySelector('.summary__item-name').innerHTML = `${product.name} - ${cart[product.id]} шт`;
        summaryItem.querySelector('.summary__item-price').innerHTML = `${Number(product.price) * cart[product.id]} руб`;
        summaryItemsContainer.appendChild(summaryItem);
    })
}

async function syncCartWithServer(ids) {
    // Fetch to server to get info about products
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
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
    // Delete missing products in cart after server responce (basic is productsIds)
    // Если что-то добавили в LS за это время, оно очистится + очистятся ошибочные id (если товар удалился например)
    // return uodated cart

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

async function initCheckout() {
    const cart = cleanProductIdsInLS();
    // TODO: редирект если корзина пустая
    
    const ids = Object.keys(cart);
    const result = await syncCartWithServer(ids);

    if (result.success) {
        const productsCache = result.data;
        console.log(productsCache);
        const currentCart = syncLSWithServerIds(productsCache.map(p => String(p.id)));
        renderSummary(productsCache, currentCart);
    } else {
        console.log(`Не удалось получить данные о товарах в корзине ${result.message}`)
    }
}
initCheckout();