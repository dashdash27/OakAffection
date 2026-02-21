// Constants:
const QUANTITY_MAX = 30;

let productsCache = null;

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
        console.log("Корзина была очищена от некорректных данных");
    }
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
function removeItemFromCart(id) {
    let cart = loadCartFromLS();
    delete cart[id];
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
        cart[id] = Number(cart[id]) + Number(delta);

        if (cart[id] > QUANTITY_MAX) {
            cart[id] = QUANTITY_MAX;
            return;
        }

        if (cart[id] <= 0) {
            cart[id] = 1;
            return;
        }
        else {
            localStorage.setItem('cart', JSON.stringify(cart));
            syncProductStateUI(id, cart);
            cartChannel.postMessage({ 
                productId: id,
                newCart: cart
            });
        }
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
}

function renderCart(products) {
    const cartItemsContainer = document.querySelector('.cart__items');
    const cartItemTemplate = document.querySelector('.cart__item-template');

    cartItemsContainer.innerHTML = "";

    if (products.length === 0) {
        cartItemsContainer.innerHTML = 'Корзина пуста';
        return;
    }

    const cart = loadCartFromLS();

    let totalAmount = 0;

    products.forEach(product => {
        const clone = cartItemTemplate.content.cloneNode(true);
        const cartItem = clone.querySelector('.cart__item');
        
        // если данные разошлись с LS
        if (!cart[product.id]) return; 

        cartItem.dataset.id = product.id;

        cartItem.querySelector('.cart__item-name').textContent = product.name;
        cartItem.querySelector('.cart__item-name').href = `/product/${product.slug}`;
        cartItem.querySelector('.cart-item__count').textContent = cart[product.id];
        const cartItemTotal = Number(product.price) * cart[product.id];
        cartItem.querySelector('.cart__item-total').textContent = `${cartItemTotal.toLocaleString('ru-RU')} ₽`;
        
        const cartItemImg = cartItem.querySelector('.cart__item-img');
        cartItemImg.src = product.photo_path;
        cartItemImg.onerror = () => { 
            cartItemImg.src = '/static/img/icons/nophoto.png'; 
            cartItemImg.onerror = null;
        };

        cartItemsContainer.appendChild(cartItem);

        totalAmount += cartItemTotal;
    })
    document.querySelector('.cart__total-amount').textContent = `${totalAmount.toLocaleString('ru-RU')} ₽`;
}

async function syncCartWithServer(ids) {
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

async function initCartSystem() {
    cleanProductIdsInLS();
    const cart = loadCartFromLS();

    if (window.location.pathname.includes('/cart')) {
        const ids = Object.keys(cart);
        const result = await syncCartWithServer(ids);

        if (result.success) {
            productsCache = result.data;
            syncLSWithServerIds(productsCache.map(p => String(p.id)))
            renderCart(productsCache);
        } else {
            console.log(`Не удалось получить данные о товарах в корзине ${result.message}`)
        }
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
    // 1 - product cards
    const card = document.querySelector(`.card[data-id="${id}"]`);
    if (card) {
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

    // 3 - Cart Item
    const cartItem = document.querySelector(`.cart__item[data-id="${id}"]`);
    if (cartItem) {
        if (id in cart) {
            const countLabel = cartItem.querySelector('.cart-item__count');
            if (countLabel) countLabel.textContent = cart[id];

            // recount total cart-item
            const totalLabel = cartItem.querySelector('.cart__item-total');
            const productPrice = Number(productsCache.find(p => String(p.id) === String(id)).price);
            if (totalLabel) totalLabel.textContent = `${(cart[id] * productPrice).toLocaleString('ru-RU')} ₽`;
        }
        else {
            cartItem.remove()
        }

        // Recount total cart amount
        const totalAmount = productsCache.reduce((sum, product) => {
            const count = cart[product.id] || 0;
            return sum + (Number(product.price) || 0) * count;
        }, 0);
        document.querySelector('.cart__total-amount').textContent = `${totalAmount.toLocaleString('ru-RU')} ₽`;
        
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

    // 5. Counter - in cart item
    const cartItemMinus = e.target.closest('.cart-item__btn-minus');
    if (cartItemMinus) {
        e.preventDefault();
        const product = cartItemMinus.closest('.cart__item');
        const productId = product.dataset.id;

        updateCartItemQuantity(productId, -1);
        return;
    }

    // 6. Counter + in cart item
    const cartItemPlus = e.target.closest('.cart-item__btn-plus');
    if (cartItemPlus) {
        e.preventDefault();
        const product = cartItemPlus.closest('.cart__item');
        const productId = product.dataset.id;

        updateCartItemQuantity(productId, 1);
        return;
    }

    // 7. Delete cart item
    const removeCartItemBtn = e.target.closest('.cart__item-remove');
    if (removeCartItemBtn) {
        e.preventDefault();
        const product = removeCartItemBtn.closest('.cart__item');
        const productId = product.dataset.id;

        removeItemFromCart(productId);
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