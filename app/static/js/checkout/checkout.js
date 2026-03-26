const checkoutState = {
    currentCitySuggestions: [],
    selectedCity: null,
    deliveryOptions: null,
    selectedDeliveryOption: null,
    selectedPvz: null
}
// Elements
const checkoutSection = document.querySelector('.checkout');
const cityInput = document.querySelector('.city-input');
const citySuggestions = document.querySelector('.city-suggestions');
const deliveryOptions = document.querySelector('.checkout__delivery-options');
const pvzSearchInput = document.querySelector('.pvz-input');
const pvzSuggestions = document.querySelector('.pvz-suggestions');

// Обновление интерфейса при редактировании/сбрасывании данных
function changeCheckoutState(state) {
    checkoutSection.dataset.step = state;

    if (state === "city-choice") {
        checkoutState.selectedCity = null;
        checkoutState.deliveryOptions = null;
        checkoutState.selectedDeliveryOption = null;
        checkoutState.selectedPvz = null;

        cityInput.value = "";
        citySuggestions.innerHTML = "";
        deliveryOptions.innerHTML = "Доставки появятся после выбора города";
        pvzSuggestions.innerHTML = "ПВЗ появляется после заполнения города и выбора доставки";

        return
    }
    if (state === "delivery-choice") {
        checkoutState.selectedDeliveryOption = null;
        checkoutState.selectedPvz = null;

        citySuggestions.innerHTML = "";
        pvzSuggestions.innerHTML = "ПВЗ появляется после заполнения выбора доставки";

        return
    }
    if (state === "pvz-choice") {
        checkoutState.selectedPvz = null;

        pvzSearchInput.value = "";
        renderPvzSuggestions(checkoutState.selectedDeliveryOption.points);

        return
    }
    if (state === "contacts") {
        pvzSuggestions.innerHTML = "";
    }
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
    setTimeout(() => {
        if (!checkoutState.selectedCity) {
            changeCheckoutState("city-choice");
        }
    }, 300);
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
    setTimeout(() => {
        if (!checkoutState.selectedPvz) {
            changeCheckoutState("pvz-choice");
        }
    }, 300);
});

checkoutSection.addEventListener('click', (e) => {
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
const phoneInput = document.querySelector('.phone-input');
const phoneMask = IMask(phoneInput, {
  mask: '+{7}(000)000-00-00'
});