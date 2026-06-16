window.Checkout = window.Checkout || {};

window.Checkout.config = {
    DELIVERY_STYLES: {
        yandex: { color: '#FFCC00', label: 'Я' },
        post: { color: '#0055A5', label: 'П' }
    },
    QUANTITY_MAX: 30
};

window.Checkout.state = {
    currentCitySuggestions: [],
    selectedCity: null,
    deliveryOptions: null,
    selectedDeliveryOption: null,
    selectedPvz: null,
    contacts: { name: null, phone: null, email: null },
    cart: null,
    step: null,
    productsCache: null,
    itemsTotal: null,
    discountMultiplier: 0,
    discountLabel: null,
    totalPrice: null
};