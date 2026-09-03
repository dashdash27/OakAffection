def extract_city_context(raw_address: str) -> str:
    """
    Вырезает первые 3 элемента адреса Ozon для точной группировки локаций.
    Приводит строку к нижнему регистру и очищает от лишних пробелов.
    Пример:
    'Россия, Московская обл, Балашиха г, улица Свердлова, 16' -> 'россия московская обл балашиха г'
    """
    if not raw_address:
        return ""
    
    parts = [p.strip().lower() for p in raw_address.split(",")]
    context_parts = parts[:3]
    str_context = " ".join(context_parts).strip()
    
    return str_context