
YANDEX_DELIVERY_CONFIG = {
    "points_profiles": {
        # Обычные ПВЗ Яндекса
        "point": {
            "order": {"weight": 200000, "sum": 500, "side": 300},
            "box":   {"weight": 30000,  "sum": 300, "side": 150}
        },
        # ПВЗ Пятерочки (5Post)
        "five_post_postamat": {
            "order": {"weight": 200000, "sum": 500, "side": 300},
            "box":   {"weight": 15000,  "sum": 136, "side": 64}
        },
        # Постаматы Яндекса
        "postamat": {
            "order": {"weight": 20000,  "sum": 118, "side": 40},
            "box":   {"weight": 20000,  "sum": 118, "side": 40}
        }
    },
    "remote_region_limits": {
        "weight": 15000,  # 15 кг
        "sum": 180,       # 180 см
        "side": 60        # 60 см
    },
    # Remote regions
    "remote_regions_dadata_fias_ids": {
        "844a80d6-5e31-4017-b422-4d9c01e9942c", # Амурская область
        "6466c988-7ce3-45e5-8b97-90ae16cb1249", # Иркутская область
        "43909681-d6e1-432d-b61f-ddac393cb5da", # Приморский край
        "7d468b39-1afa-41ec-8c4f-97a8603cb3d4", # Хабаровский край
        "294277aa-e25d-428c-95ad-46719c4ddb44", # Архангельская область
        "1c727518-c96a-4f34-9ae6-fd510da3be03", # Мурманская область
        "248d8071-06e1-425e-a1cf-d1ff4c4a14a8", # Республика Карелия
        "c20180d9-ad9c-46d1-9eff-d60bc424592a", # Республика Коми
        "8d3f1d35-f0f4-41b5-b5b7-e7cadf3e7bd7", # Республика Хакасия
    }
}


def get_allowed_yandex_profiles(order_dimensions: dict, dadata_region_fias_id: str) -> list:
    """Pre-filtering types of yandex pickup points types"""
    is_remote = dadata_region_fias_id in YANDEX_DELIVERY_CONFIG["remote_regions_dadata_fias_ids"]
    allowed_profiles = []

    print("Remote:", is_remote)

    total_weight = order_dimensions["total_weight"]
    cubic_sum_of_sides = order_dimensions["cubic_sum_of_sides"]
    max_item_side = order_dimensions["max_item_side"]
    max_item_weight = order_dimensions["max_item_weight"]

    if total_weight == 0:
        return allowed_profiles

    for profile_name, limit in YANDEX_DELIVERY_CONFIG["points_profiles"].items():
        order_lim = limit["order"]
        box_lim = limit["box"]

        if is_remote:
            remote_lim = YANDEX_DELIVERY_CONFIG["remote_region_limits"]
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
        
        is_point_allowed = False

        # Проверяем совпадение по ключевым словам
        if "point" in allowed_profiles:
            if "пункт выдачи" in point_name or "пвз" in point_name:
                is_point_allowed = True
                
        if "five_post_postamat" in allowed_profiles:
            if "5 post" in point_name or "5post" in point_name or "пятерочк" in point_name:
                is_point_allowed = True
                
        if "postamat" in allowed_profiles:
            if "постамат" in point_name and "маркет" in point_name:
                if "5 post" not in point_name and "5post" not in point_name:
                    is_point_allowed = True

        if is_point_allowed:
            filtered_points.append(point)
    
    return filtered_points