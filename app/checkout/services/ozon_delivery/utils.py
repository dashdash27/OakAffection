from app.logger import logger

import re

def determine_shipment_method_id(order_dimensions: dict, ozon_delivery_cfg: dict) -> int:
    """Расчет в граммах и см"""

    weight = order_dimensions["total_weight"]
    cubic_sum_of_sides = order_dimensions["cubic_sum_of_sides"]
    max_item_side = order_dimensions["max_item_side"]

    # 1. Распределяем общую кубическую сумма сторон на 3 измерения
    base_side = cubic_sum_of_sides / 3

    length = max(base_side, max_item_side)
    width = base_side
    height = base_side

    # 2. Вычисляем объем в литрах
    volume_liters = (length * width * height) / 1000

    max_weight = ozon_delivery_cfg.get("GLOBAL_MAX_WEIGHT_LIMIT", 125000)
    max_side_a = ozon_delivery_cfg.get("MAX_SIDE_A_LIMIT", 120)
    max_side_b = ozon_delivery_cfg.get("MAX_SIDE_B_LIMIT", 220)
    max_side_c = ozon_delivery_cfg.get("MAX_SIDE_C_LIMIT", 240)

    # 3. Проверка на длины сторон и вес - если не проходит, доставка недоступна
    sorted_sides = sorted([length, width, height])
    if (weight > max_weight or 
        sorted_sides[0] > max_side_a or   # Самая маленькая сторона коробки > 120 см
        sorted_sides[1] > max_side_b or   # Средняя сторона коробки > 220 см
        sorted_sides[2] > max_side_c):    # Самая большая сторона коробки > 240 см
        return None

    # 4. Проверка на крупногабарит - пока делаем недоступной
    kgt_weight = ozon_delivery_cfg.get("KGT_THRESHOLD_WEIGHT_LIMIT", 35000)
    kgt_side = ozon_delivery_cfg.get("KGT_THRESHOLD_SIDE_LIMIT", 200)
    kgt_volume = ozon_delivery_cfg.get("KGT_THRESHOLD_VOLUME_LIMIT", 500)

    if (weight >= kgt_weight or 
        length >= kgt_side or width >= kgt_side or height >= kgt_side or 
        volume_liters >= kgt_volume):
        return None

    return ozon_delivery_cfg.get('REGULAR_SHIPMENT_METHOD_ID')


def extract_city_context(raw_address: str) -> str:
    if not raw_address:
        return ""

    # 1. Убираем почтовый индекс (6 цифр)
    clean_address = re.sub(r'\b\d{6}\b', '', raw_address)
    
    # 2. Приводим к нижнему регистру и стираем точки (запятые пока ОСТАВЛЯЕМ на месте)
    clean_address = clean_address.lower().replace('.', '')

    # 3. Маркеры улиц и дорог
    stop_markers = [
        r'\bулица\b', r'\bул\b', r'\bпроспект\b', r'\bпр-кт\b', r'\bпркт\b', r'\bпросп\b', 
        r'\bбульвар\b', r'\bб-вар\b', r'\bпереулок\b', r'\bпер\b', r'\bшоссе\b', r'\bш\b',
        r'\bтракт\b', r'\bнабережная\b', r'\bпроезд\b', r'\bаллея\b', r'\bквартал\b', r'\bлиния\b',
        r'\bдом\b', r'\bд\b', r'\bстр\b', r'\bкорпус\b', r'\bкорп\b', r'\bстроение\b', r'\bмикрорайон\b', r'\bмкр\b',
        r'\bплощадь\b',

        r'\bк\d+',
        r'\b\d+[a-яa-z]\b'
    ]

    # Находим, какой маркер встретился в строке самым первым
    first_marker_pos = len(clean_address)
    for marker in stop_markers:
        match = re.search(marker, clean_address, flags=re.UNICODE)
        if match and match.start() < first_marker_pos:
            first_marker_pos = match.start()

    # 4. ЛОГИКА С ЗАПЯТОЙ: Если маркер найден, ищем запятую ПЕРЕД ним
    if first_marker_pos < len(clean_address):
        # Берем кусок строки ДО маркера улицы
        string_before_marker = clean_address[:first_marker_pos]
        
        # Находим индекс ПОСЛЕДНЕЙ запятой в этом куске
        last_comma_pos = string_before_marker.rfind(',')
        
        # Если запятая перед улицей найдена, режем строго по неё
        if last_comma_pos != -1:
            short_address = string_before_marker[:last_comma_pos].strip()
        else:
            # Если запятой вдруг не было (слова написаны слитно), режем по сам маркер
            short_address = string_before_marker.strip()
    else:
        short_address = clean_address.strip()

    # 5. Теперь, когда всё лишнее отрезано, заменяем оставшиеся внутренние запятые на пробелы
    short_address = short_address.replace(',', ' ')

    # 6. Финальное удаление случайных двойных пробелов
    short_address = re.sub(r'\s+', ' ', short_address)

    return short_address