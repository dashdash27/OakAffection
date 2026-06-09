def get_search_radius_by_fias_level(fias_level: int) -> int:
    if fias_level == 1:
        return 50
    elif fias_level == 4:
        return 10
    else:
        return 30
    
def get_filtered_russian_post_points_by_exact_city(api_points: list, city_data: dict) -> list:
    dadata_city = city_data.get('settlement')
    clean_dadata_city = dadata_city.lower().strip()

    if not clean_dadata_city:
        return api_points
    
    filtered_points = []
    for point in api_points:
        point_settlement = point.get('settlement') or ""
        clean_point_settlement = point_settlement.lower().strip()

        if clean_point_settlement == clean_dadata_city:
            point_type_code = (point.get('type-code') or "").upper()
            
            if "ПОЧТОМАТ" in point_type_code:
                continue
            
            filtered_points.append(point)

    return filtered_points