// Helpers
function loadCartFromLS() {
    return JSON.parse(localStorage.getItem('cart')) || {};
}
function addItemToCart(id) {
    let cart = loadCartFromLS();

    if (!cart[id]) {
        cart[id] = 1;
    }

    localStorage.setItem('cart', JSON.stringify(cart));
    syncProductStateUI(id, cart);
    cartChannel.postMessage({ 
        productId: id,
        newCart: cart
    });
}

function initCartSystem() {
    // cleanProductIdsInLS();
    const cart = loadCartFromLS();
    document.querySelectorAll('.card').forEach(card => {
        syncProductStateUI(card.dataset.id, cart);
    });
}

function syncProductStateUI(id, cart) {
    const idsInCart = Object.keys(cart);

    // 1 - карточки товаров
    const card = document.querySelector(`.card[data-id="${id}"]`);
    if (card) {
        console.log(`Элемент найден ${id}`);
        if (id in cart) {
            card.setAttribute('data-cart-state', 'in-cart');
        }
        else {
            card.setAttribute('data-cart-state', 'idle');
        } 
    }
}

// Обработчик кликов
document.addEventListener('click', (e) => {
    // 1. Cart-add
    const cardCartAdd = e.target.closest('.card__cart-add');
    if (cardCartAdd) {
        e.preventDefault();
        const card = cardCartAdd.closest('.card');
        const productId = card.dataset.id;
        console.log(`Клик по продукту ${productId}`);

        addItemToCart(productId);
        return; 
    }
})

// Tabs connect
const cartChannel = new BroadcastChannel('cart_updates');
cartChannel.onmessage = (event) => {
    const { productId, newCart } = event.data;
    const cart = newCart || loadCartFromLS();
    console.log(`Получено обновление из другой вкладки: для товара ${productId}`);
    syncProductStateUI(productId, cart);
};

document.addEventListener('DOMContentLoaded', initCartSystem);