const checkoutSection = document.querySelector('.checkout');
const checkoutState = {
    currentCitySuggestions: [],
    selectedCity: null
}

// City 
let debounceTimer;
const cityInput = document.querySelector('.city-input');
const citySuggestions = document.querySelector('.city-suggestions');

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
            checkoutState.currentCitySuggestions = []
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
            <div class="checkout__suggestion-item" 
                 data-index="${index}">
                 ${city.value}
            </div>
        `;
    }).join('');
}

checkoutSection.addEventListener('click', (e) => {
    const item = e.target.closest('.checkout__suggestion-item');
    if (item) {
        const index = parseInt(item.dataset.index);
        const cityObject = checkoutState.currentCitySuggestions[index];

        checkoutState.selectedCity = cityObject;

        // скрываем блок с подсказками
        cityInput.value = checkoutState.selectedCity.value;
        citySuggestions.innerHTML = "";
        checkoutSection.dataset.step = "delivery-choice";

        console.log("Список предложений городов:", checkoutState.currentCitySuggestions);
        console.log("Вбыранный город:", checkoutState.selectedCity);
    }
});

// Потеря фокуса (blur)
cityInput.addEventListener('blur', () => {
    setTimeout(() => {
        if (!checkoutState.selectedCity) {
            checkoutSection.dataset.step = "city";
            citySuggestions.innerHTML = "";
            cityInput.value = "";
        }
    }, 300);
});