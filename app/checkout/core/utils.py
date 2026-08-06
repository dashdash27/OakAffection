from app.checkout.utils import process_cart, calculate_cart_base_total, apply_threshold_discount
from app.logger import logger

import os
import jwt
import hmac
import hashlib

def verify_and_get_delivery_price(delivery_token: str) -> int:
    """Проверяет JWT токен доставки и возвращает проверенную сервером цену."""
    secret_key = os.getenv("SECRET_KEY")
    try:
        decoded_delivery = jwt.decode(delivery_token, secret_key, algorithms=["HS256"])
        logger.debug("Проверка токена доставки прошла успешно.")
        return int(decoded_delivery.get("price"))
    except jwt.ExpiredSignatureError:
        logger.warning("Время действия докена доставки истекло.")
        raise ValueError("Время действия тарифа доставки истекло.")
    except jwt.InvalidTokenError:
        logger.warning("Ошибка во время проверки токена доставки.")
        raise ValueError("Ошибка во время проверки токена доставки.")
    
def validate_order_totals(cart, trusted_delivery_price: int, client_total_amount: int) -> tuple[bool, list, int, int]:
    """
        Считает серверную стоимость и сверяет с клиентом
        Возвращает: (совпадает_ли_сумма, order_items, discount_amount, items_discounted_total)
    """
    order_items = process_cart(cart)
    items_base_total = calculate_cart_base_total(order_items)
    items_discounted_total = apply_threshold_discount(items_base_total)
    discount_amount = items_base_total - items_discounted_total
    
    server_total_amount = items_discounted_total + trusted_delivery_price

    is_valid = (client_total_amount == server_total_amount)

    return is_valid, order_items, discount_amount, items_discounted_total

def allocate_items_discount(order_items: list, items_base_total: int, items_discounted_total: int) -> list:
    """
    Шаг 4: Распределяет скидку по товарам и корректирует рублевую погрешность.
    Если скидки нет (коэффициент = 1), функция просто вернет исходный список.
    """
    if items_base_total == items_discounted_total:
        for item in order_items:
            item["price_with_discount"] = item["price"]
        return order_items
    
    discount_coefficient = items_discounted_total / items_base_total
    allocated_sum = 0

    for item in order_items:
        item_discounted_price = round(item["price"] * discount_coefficient)
        item["price_with_discount"] = item_discounted_price
        allocated_sum += item_discounted_price * item["quantity"]

    rubles_difference = items_discounted_total - allocated_sum
    if rubles_difference != 0 and len(order_items) > 0:
        corrected = False

        # Сценарий А: Ищем товар с количеством 1
        for item in order_items:
            if item["quantity"] == 1:
                item["price_with_discount"] += rubles_difference
                corrected = True
                break

         # Сценарий Б: Оптовый случай — разбиваем первую строку
        if not corrected:
            first_item = order_items[0]
            first_item["quantity"] -= 1
            
            adjusted_item = first_item.copy()
            adjusted_item["quantity"] = 1
            adjusted_item["price_with_discount"] += rubles_difference
            
            order_items.insert(0, adjusted_item)

    return order_items

def generate_order_hash(order_id: int) -> str:
    """Генерирует уникальный токен для ID заказа на основе SECRET_KEY."""
    secret_key = os.getenv("SECRET_KEY").encode('utf-8') 
    message = str(order_id).encode('utf-8')
    return hmac.new(secret_key, message, hashlib.sha256).hexdigest()

def verify_order_hash(order_id: int, client_hash: str) -> bool:
    """Безопасно сверяет токен заказа от клиента с ожидаемым."""
    if not client_hash:
        return False
    expected_hash = generate_order_hash(order_id)
    return hmac.compare_digest(expected_hash, client_hash)