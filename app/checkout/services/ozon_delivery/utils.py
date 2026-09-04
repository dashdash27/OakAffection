from app.logger import logger

import re

def determine_shipment_method_id(order_dimensions: dict, ozon_delivery_cfg: dict) -> int:
    """Расчет в граммах и см"""
    logger.debug(f"Order dimensions: {order_dimensions}")

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

    # 3. Проверка на длины сторон и вес - если не проходит, доставка недоступна
    sorted_sides = sorted([length, width, height])
    if (weight > 125000 or 
        sorted_sides[0] > 120 or   # Самая маленькая сторона коробки > 120 см
        sorted_sides[1] > 220 or   # Средняя сторона коробки > 220 см
        sorted_sides[2] > 240):    # Самая большая сторона коробки > 240 см
        logger.debug("Доставка Ozon недоступна")
        return None

    # 4. Проверка на крупногабарит
    if (weight >= 35000 or 
        length >= 200 or width >= 200 or height >= 200 or 
        volume_liters >= 500):
        logger.debug("Крупногабаритная доставка")
        return ozon_delivery_cfg.get('KGT_SHIPMENT_METHOD_ID')

    logger.debug("Обычная доставка")
    return ozon_delivery_cfg.get('REGULAR_SHIPMENT_METHOD_ID')


def extract_city_context(raw_address: str) -> str:
    """
    Отрезает адрес строго на уровне населенного пункта.
    Игнорирует индексы, улицы, дома, корпуса, сохраняя только 
    цепочку: Страна -> Регион -> Район -> Город.
    """
    if not raw_address:
        return ""

    # Убираем индексы
    clean_address = re.sub(r'\b\d{6}\b', '', raw_address)

    # Разделяем адрес на элементы по запятым
    parts = [p.strip() for p in clean_address.split(",") if p.strip()]

    # Если в части адреса есть такая часть - отсекаем ее
    trash_markers = [
        'улица', 'ул', 'проспект', 'пр-кт', 'пркт', 'бульвар', 'б-вар', 
        'переулок', 'пер', 'шоссе', 'ш', 'дом', 'д ', 'д.', 'кв', 'офис', 
        'строение', 'стр', 'корпус', 'корп', 'лит', 'литера', 'пвз'
    ]

    context_parts = []

    for part in parts:
        # Нижний регистр и стирание точек
        part_clean = part.lower().replace('.', '').strip()

        if re.match(r'^\d+$', part_clean) or re.match(r'^\d+[\s\-/a-яА-Я\d]+', part_clean):
            continue

        has_trash = any(re.search(r'\b' + re.escape(marker) + r'\b', part_clean) for marker in trash_markers)

        if has_trash or re.search(r'\b[дш]\b', part_clean):
            continue
            
        context_parts.append(part_clean)

    str_context = " ".join(context_parts).strip()
    
    # Шаг 7: Удаление случайных двойных пробелов
    str_context = re.sub(r'\s+', ' ', str_context)
    
    return str_context