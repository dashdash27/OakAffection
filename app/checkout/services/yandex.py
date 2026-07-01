import json
import math

from app.logger import logger
from ..utils import format_delivery_days, normalize_and_ceil_price
from .yandex_delivery_utils import get_allowed_yandex_profiles, get_filtered_yandex_points


async def get_yandex_delivery_info(city_data, order_dimensions, client, yandex_cfg: dict):
    api_token = yandex_cfg.get('API_TOKEN')
    source_point_id = yandex_cfg.get('SOURCE_PVZ_ID')
    auth_headers = {"Authorization": f"Bearer {api_token}"}

    print("Yandex delivery info request...")

    try:
        geo_id = await _detect_geo_id(city_data, client, auth_headers, yandex_cfg)
        
        if not geo_id:
            return {
                "status": "business_error",
                "error_code": "NO_REGION_ID",
                "message": "Не удалось определить geo_id для данного города."
            }
        
        print("-- Yandex Geo id:", geo_id)
        
        points = await  _get_pickup_points(geo_id, client, auth_headers, yandex_cfg)
        if not points:
            return {
                "status": "business_error",
                "error_code": "NO_POINTS_IN_REGION",
                "message": "В данном городе нет ПВЗ Яндекса"
            }
        
        # 1 - get allowed profiles to order
        allowed_profiles = get_allowed_yandex_profiles(order_dimensions, city_data.get('region_fias_id'), yandex_cfg)
        # 2 - filter points by allowed profiles
        filtered_points = get_filtered_yandex_points(points, allowed_profiles)
        # sort points by priority: 5Post -> end
        filtered_points.sort(key=lambda x: x.get("_matched_profile") == "five_post_postamat")

        print("-- Yandex Allowed profiles:", allowed_profiles)
        print("-- Yandex all points (qty):", len(points))
        print("-- Yandex filtered points (qty):", len(filtered_points))
        
        if not filtered_points:
            return {
                "status": "business_error",
                "error_code": "OVERSIZE_OR_OVERWEIGHT",
                "message": "Заказ слишком тяжелый или объемный для ПВЗ в вашем регионе."
            }
        
        # 3 - get delivery details
        details = None
        for test_point in filtered_points[:3]:
            try:
                details = await _get_delivery_details(
                    source_point_id, 
                    test_point.get('id'),
                    order_dimensions, 
                    client, 
                    auth_headers,
                    yandex_cfg
                )
                if details and details.get('price'):
                    break
            except Exception as calc_error:
                continue

        if not details or not details.get('price'):
            print("Яндекс: Не удалось рассчитать цену для региона", city_data.get('value'))
            logger.warning(f"Яндекс: Не удалось рассчитать цену для региона {city_data.get('value')}")
            return {
                "status": "tech_error",
                "error_code": "PRICE_CALCULATION_FAILED",
                "message": "Не удалось рассчитать стоимость доставки у Яндекса."
            }
        
        print("-- Yandex delivery details:", json.dumps(details, indent=4))
        
        delivery_days = format_delivery_days(details.get('delivery_days'))
        clean_price = normalize_and_ceil_price(details.get('price'))
        multiplier = yandex_cfg.get('MARGIN_MULTIPLIER', 1.0)
        clean_price_with_margin = math.ceil(multiplier* clean_price)

        if clean_price is None:
            print("Яндекс: Ошибка парсинга цены. details.price равен None или некорректен.")
            logger.error("Яндекс: Ошибка парсинга цены. details.price равен None или некорректен.")
            return {
                "status": "tech_error",
                "error_code": "PRICE_PARSING_FAILED",
                "message": "Не удалось рассчитать стоимость доставки у Яндекса.",
                "points": []
            }
        
        return {
            "status": "success",
            "error_code": None,
            "name": "Яндекс Доставка",
            "points": filtered_points,
            "delivery_days": delivery_days,
            "price": clean_price_with_margin
        }
    
    except Exception as e:
        print(f"Критическая ошибка во время интеграции с Яндекс Доставкой: {e}")
        logger.error(f"Критическая ошибка во время интеграции с Яндекс Доставкой: {e}", exc_info=True)
        return {
            "status": "tech_error",
            "error_code": "YANDEX_API_DOWN",
            "message": "Сервер службы доставки Яндекса временно недоступен.",
            "points": []
        }

async def _detect_geo_id(city_data, client, headers, yandex_cfg: dict):
    url = yandex_cfg.get('URL_GEO_ID')
    payload = {
        "location": city_data.get('value')
    }

    response = await client.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()
    variants = data.get('variants', [])

    if not variants:
        return None
    
    first_variant = variants[0]
    return first_variant.get('geo_id')
    
async def _get_pickup_points(geo_id, client, headers, yandex_cfg: dict):
    url = yandex_cfg.get('URL_POINTS_LIST')
    payload = {
        "geo_id": geo_id
    }

    response = await client.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()

    raw_points = data.get('points', [])

    if not raw_points:
        return None
    
    formatted_points = []
    for p in raw_points:
        formatted_points.append({
            "id": p.get('id'),
            "address": p.get('address', {}).get('full_address'),
            "name": p.get('name')
        })
        
    return formatted_points

async def _get_delivery_details(source_point_id, destination_point_id, order_dimensions, client, headers, yandex_cfg: dict):
    url = yandex_cfg.get('URL_PRICING_CALCULATOR')

    SAFE_BOX_WEIGHT = yandex_cfg.get('SAFE_BOX_WEIGHT', 20)
    total_weight = order_dimensions['total_weight']
    number_of_places = math.ceil(total_weight / SAFE_BOX_WEIGHT)
    places = []
    remaining_weight = total_weight
    big_cube_side = order_dimensions['cubic_sum_of_sides'] / 3

    if number_of_places > 1:
        avg_side = max(1, math.ceil(big_cube_side / math.pow(number_of_places, 1/3)))
    else:
        avg_side = max(1, math.ceil(big_cube_side))

    for i in range(number_of_places):
        if i == number_of_places - 1:
            place_weight = remaining_weight
        else:
            place_weight = int(total_weight / number_of_places)
            remaining_weight -= place_weight
            
        places.append({
            "physical_dims": {
                "weight_gross": place_weight,
                "dx": avg_side,
                "dy": avg_side,
                "dz": avg_side
            }
        })


    payload = {
        "destination": {
            "platform_station_id": destination_point_id
        },
        "source": {
            "platform_station_id": source_point_id
        },
        "tariff": "self_pickup",
        "total_weight": total_weight,
        "places": places
    }
    
    response = await client.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()

    delivery_days = data.get('delivery_days')
    price = data.get('pricing_total')

    return {
        "delivery_days": delivery_days,
        "price": price
    }