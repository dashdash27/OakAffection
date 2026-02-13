// Helpers
function loadCartFromLS() {
    return JSON.parse(localStorage.getItem('cart')) || {};
}
function addItemToCart(id) {
    let cart = loadCartFromLS();

    if (!(id in cart)) {
        cart[id] = 1;
    }

    localStorage.setItem('cart', JSON.stringify(cart));
    syncProductStateUI(id, cart);
    cartChannel.postMessage({ 
        productId: id,
        newCart: cart
    });
}
function updateCartItemQuantity(id, delta) {
    let cart = loadCartFromLS();
    if (id in cart) {
        cart[id] += delta;
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

    // 1 - product cards
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

    // 2 - product details
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
    // 1. Cart-add in card
    const cardCartAdd = e.target.closest('.card__cart-add');
    if (cardCartAdd) {
        e.preventDefault();
        const card = cardCartAdd.closest('.card');
        const productId = card.dataset.id;

        addItemToCart(productId);
        return; 
    }

    // 2. Cart-add in product details
    const productCartAdd = e.target.closest('.product__cart-add');
    if (productCartAdd) {
        e.preventDefault();
        const product = productCartAdd.closest('.product');
        const productId = product.dataset.id;

        addItemToCart(productId);
        return;
    }

    // 3. Counter + in product details
    const productQtyPlus = e.target.closest('.qty-btn-plus');
    if (productQtyPlus) {
        e.preventDefault();
        const product = productQtyPlus.closest('.product');
        const productId = product.dataset.id;

        updateCartItemQuantity(productId, 1);
        return;
    }

    // 4. Counter - in product details
    const productQtyMinus = e.target.closest('.qty-btn-minus');
    if (productQtyMinus) {
        e.preventDefault();
        const product = productQtyMinus.closest('.product');
        const productId = product.dataset.id;

        updateCartItemQuantity(productId, -1);
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