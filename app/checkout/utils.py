from app.models import Product

import math
import re
from flask import current_app

DISCOUNT_THRESHOLDS = [
    (30000, 25),
    (10000, 20),
]

def pluralize(number, titles):
    cases = [2, 0, 1, 1, 1, 2]
    if 4 < number % 100 < 20:
        idx = 2
    else:
        idx = cases[min(number % 10, 5)]
    return f"{number} {titles[idx]}"

def format_delivery_days(api_days):
    try:
        # 1. Если API прислало число (например, 7)
        min_days = int(api_days)
        max_days = min_days + 1  # Твой запас для безопасности
        
        # 2. Склоняем по максимальному числу
        word = ["день", "дня", "дней"]
        
        if min_days == max_days:
             return pluralize(min_days, word)
             
        # Возвращаем красивую строку: "7-8 дней"
        day_word = pluralize(max_days, word).split()[-1] 
        return f"{min_days}-{max_days} {day_word}"
        
    except (ValueError, TypeError):
        return "срок уточняется"
    
def process_cart(cart):
    clean_ids = []
    for pid in cart.keys():
        try:
            clean_ids.append(int(pid))
        except (ValueError, TypeError):
            continue
    
    products = Product.query.filter(Product.id.in_(clean_ids)).all()

    parcel_fallbacks_cfg = current_app.config['PARCEL_FALLBACKS']

    order_items = []
    for p in products:
        w = p.wrapper
        order_items.append({
            "id": p.id,
            "name": p.name,
            "quantity": cart.get(str(p.id)) or cart.get(p.id),
            "price": p.price,
            "weight": p.weight if getattr(p, "weight", None) else parcel_fallbacks_cfg.get('PRODUCT_WEIGHT_G'),
            "length": w.length if w else parcel_fallbacks_cfg.get('WRAPPER_LENGTH_CM'),
            "height": w.height if w else parcel_fallbacks_cfg.get('WRAPPER_HEIGHT_CM'),
            "depth": w.depth if w else parcel_fallbacks_cfg.get('WRAPPER_DEPTH_CM'),
        })

    return order_items

    
def calculate_order_dimensions(cart_items):
    """Approximately order params"""
    total_weight = 0
    total_volume = 0
    max_item_side = 0
    max_item_weight = 0
    cubic_sum_of_sides = 0

    factors = current_app.config.get("DELIVERY_SAFETY_FACTORS", {})

    for item in cart_items:
        q = item['quantity']
        w, l, h, d = item['weight'], item['length'], item['height'], item['depth']

        total_weight += w * q
        total_volume += (l * h * d) * q

        # find the biggest item-side and the biggest item-wrapper weight
        max_item_side = max(max_item_side, l, h, d)
        max_item_weight = max(max_item_weight, w)

    if total_volume > 0:
        side = math.pow(total_volume, 1/3)
        cubic_sum_of_sides = math.ceil(side * 3 * factors.get("CUBIC_SUM", 1.0))

    total_weight = math.ceil(total_weight * factors.get("TOTAL_WEIGHT", 1.0))
    max_item_side = math.ceil(max_item_side * factors.get("MAX_ITEM_SIDE", 1.0))
    max_item_weight = math.ceil(max_item_weight * factors.get("MAX_ITEM_WEIGHT", 1.0))

    return {
            "total_weight": total_weight,
            "cubic_sum_of_sides": cubic_sum_of_sides,
            "max_item_side": max_item_side,
            "max_item_weight": max_item_weight
        }

def calculate_discounted_price(total_price) -> int:
    thresholds = current_app.config.get("DISCOUNT_THRESHOLDS", [])
    
    for step in thresholds:
        threshold = step.get("min_amount_rub", 0)
        discount_percent = step.get("discount_percent", 0)
        
        if total_price >= threshold:
            discount_amount = (total_price * discount_percent) / 100
            return math.ceil(total_price - discount_amount)
            
    return math.ceil(total_price)

def calculate_order_price(cart_items):
    total_price = 0
    for item in cart_items:
        total_price += item['price'] * item['quantity']

    return calculate_discounted_price(total_price)

def normalize_and_ceil_price(raw_price) -> int:
    if raw_price is None:
        return None
    
    try:
        price_str = str(raw_price)
        
        clean_str = re.sub(r'[^\d.,]', '', price_str)
        clean_str = clean_str.replace(',', '.')
        
        if not clean_str:
            return None
            
        return math.ceil(float(clean_str))
        
    except (ValueError, TypeError):
        return None