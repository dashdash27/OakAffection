def get_search_radius_by_fias_level(fias_level: int, post_cfg: dict) -> int:
    search_settings = post_cfg.get('GEO_SEARCH_SETTINGS', {})
    radius_map = search_settings.get("RADIUS_BY_FIAS_LEVEL", {})
    return radius_map.get(fias_level, search_settings.get("DEFAULT_RADIUS", 30))
    
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