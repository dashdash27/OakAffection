window.Checkout = window.Checkout || {};

window.Checkout.config = {
    DELIVERY_STYLES: {
        yandex: { color: '#FFCC00', label: 'Я' },
        post: { color: '#0055A5', label: 'П' }
    },
    QUANTITY_MAX: 30,
    DISCOUNT_RULES: [
        { threshold: 10000, value: 0.20, label: '20%' },
        { threshold: 30000, value: 0.25, label: '25%' }
    ].sort((a, b) => a.threshold - b.threshold)
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