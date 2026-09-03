import re

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