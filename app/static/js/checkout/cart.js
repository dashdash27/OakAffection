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

function renderCart() {
    const cartItems = document.querySelector('.cart-items');
    if (!cartItems) return;

    const cart = loadCartFromLS();
    const ids = Object.keys(cart);

    if(ids.length === 0) {
        cartItems.innerHTML = 'Корзина пуста';
        return;
    }

    let html = '<ul>';
    ids.forEach(id => {
        html += `<li>Товар #<strong>${id}</strong> — <strong>${cart[id]}</strong> шт</li>`;
    });
    html += '</ul>';

    cartItems.innerHTML = html;
}

function initCartSystem() {
    // cleanProductIdsInLS();
    const cart = loadCartFromLS();

    if (window.location.pathname.includes('/cart')) {
        renderCart();
    }
    else {
        document.querySelectorAll('.card').forEach(card => {
            syncProductStateUI(card.dataset.id, cart);
        });
        document.querySelectorAll('.product').forEach(product => {
            syncProductStateUI(product.dataset.id, cart);
        });
    }
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

    // 2 - product detail
    const product = document.querySelector(`.product[data-id="${id}"]`);
    if (product) {
        if (id in cart) {
            product.setAttribute('data-cart-state', 'in-cart');
            const countLabel = product.querySelector('.qty-value');
            if (countLabel) countLabel.textContent = cart[id];
        }
        else {
            product.setAttribute('data-cart-state', 'idle');
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