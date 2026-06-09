import math

TOTAL_WEIGHT_SAFETY_FACTOR = 1.08
MAX_ITEM_WEIGHT_SAFETY_FACTOR = 1.05
MAX_ITEM_SIDE_SAFETY_FACTOR = 1.05
CUBIC_SUM_SAFETY_FACTOR = 1.2

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
    
def calculate_order_dimensions(cart_items):
    """Approximately order params"""
    total_weight = 0
    total_volume = 0
    max_item_side = 0
    max_item_weight = 0
    cubic_sum_of_sides = 0

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
        cubic_sum_of_sides = math.ceil(side * 3 * CUBIC_SUM_SAFETY_FACTOR)

    total_weight = math.ceil(total_weight * TOTAL_WEIGHT_SAFETY_FACTOR)
    max_item_side = math.ceil(max_item_side * MAX_ITEM_SIDE_SAFETY_FACTOR)
    max_item_weight = math.ceil(max_item_weight * MAX_ITEM_WEIGHT_SAFETY_FACTOR)

    return {
            "total_weight": total_weight,
            "cubic_sum_of_sides": cubic_sum_of_sides,
            "max_item_side": max_item_side,
            "max_item_weight": max_item_weight
        }

def calculate_discounted_price(total_price):
    for threshold, discount_percent in DISCOUNT_THRESHOLDS:
        if total_price >= threshold:
            discount_amount = (total_price * discount_percent) / 100
            return math.ceil(total_price - discount_amount)
    return total_price

def calculate_order_price(cart_items):
    total_price = 0
    for item in cart_items:
        total_price += item['price'] * item['quantity']

    return calculate_discounted_price(total_price)