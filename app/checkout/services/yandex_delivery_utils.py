def get_allowed_yandex_profiles(order_dimensions: dict, dadata_region_fias_id: str, yandex_cfg: dict) -> list:
    """Pre-filtering types of yandex pickup points types"""
    is_remote = dadata_region_fias_id in yandex_cfg.get("REMOTE_REGIONS_DADATA_FIAS_IDS", {})
    allowed_profiles = []

    print("-- Remote:", is_remote)

    total_weight = order_dimensions["total_weight"]
    cubic_sum_of_sides = order_dimensions["cubic_sum_of_sides"]
    max_item_side = order_dimensions["max_item_side"]
    max_item_weight = order_dimensions["max_item_weight"]

    if total_weight == 0:
        return allowed_profiles

    for profile_name, limit in yandex_cfg.get("POINTS_PROFILES", {}).items():
        order_lim = limit["order"]
        box_lim = limit["box"]

        if is_remote:
            remote_lim = yandex_cfg.get("REMOTE_REGION_LIMITS", {})
            # Выбираем самое жесткое ограничение
            max_allowed_order_weight = min(order_lim["weight"], remote_lim["weight"])
            max_allowed_order_sum = min(order_lim["sum"], remote_lim["sum"])
            max_allowed_order_side = min(order_lim["side"], remote_lim["side"])
        else:
            # В обычном регионе лимиты остаются стандартными
            max_allowed_order_weight = order_lim["weight"]
            max_allowed_order_sum = order_lim["sum"]
            max_allowed_order_side = order_lim["side"]


        if (
            total_weight <= max_allowed_order_weight and          # Вес заказа (сжатый или обычный)
            cubic_sum_of_sides <= max_allowed_order_sum and       # Объем заказа (сжатый или обычный)
            max_item_side <= max_allowed_order_side and           # Габарит заказа (сжатый или обычный)
            max_item_weight <= box_lim["weight"] and             # Вес одной коробки/банки
            max_item_side <= box_lim["side"]                     # Габарит одной коробки/банки
        ):
            allowed_profiles.append(profile_name)
    
    return allowed_profiles

def get_filtered_yandex_points(api_points: list, allowed_profiles: list) -> list:
    """Filter yandex responce"""
    filtered_points = []

    if not allowed_profiles:
        return filtered_points
    
    for point in api_points:
        point_name = point.get("name", "").lower()
        
        matched_profile = None

        # Проверяем совпадение по ключевым словам
        if "point" in allowed_profiles:
            if "пункт выдачи" in point_name or "пвз" in point_name:
                matched_profile = "point"
                
        if "five_post_postamat" in allowed_profiles:
            if "5 post" in point_name or "5post" in point_name or "пятерочк" in point_name:
                matched_profile = "five_post_postamat"
                
        if "postamat" in allowed_profiles:
            if "постамат" in point_name and "маркет" in point_name:
                if "5 post" not in point_name and "5post" not in point_name:
                    matched_profile = "postamat"

        if matched_profile:
            point["_matched_profile"] = matched_profile
            filtered_points.append(point)
    
    return filtered_points