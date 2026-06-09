import math
from flask import current_app

from ..utils import format_delivery_days
from .russian_post_utils import get_search_radius_by_fias_level, get_filtered_russian_post_points_by_exact_city

GLOBAL_WEIGHT_LIMIT = 200000
ORDER_WEIGHT_LIMIT = 20000
MAX_SIDE_SUM = 300

async def get_russian_post_delivery_info(city_data, order_dimensions, order_price, client):
    api_token = current_app.config.get('RUSSIAN_POST', {}).get('API_TOKEN')
    api_key = current_app.config.get('RUSSIAN_POST', {}).get('API_KEY')
    index_from = current_app.config.get('RUSSIAN_POST', {}).get('INDEX_FROM')
    auth_headers = {
        "Authorization": f"AccessToken {api_token}",
        "X-User-Authorization": f"Basic {api_key}"
    }

    print("Russian Post delivery info request...")

    try:
        total_weight = order_dimensions['total_weight']

        if total_weight > GLOBAL_WEIGHT_LIMIT or order_dimensions['max_item_weight'] > ORDER_WEIGHT_LIMIT:
            return {
                "status": "business_error",
                "error_code": "OVERSIZE_OR_OVERWEIGHT",
                "message": "Заказ слишком тяжелый или объемный для доставкой Почты России"
            }

        # 1 - get points
        search_radius = get_search_radius_by_fias_level(city_data.get('fias_level'))
        latitude = city_data.get('latitude')
        longitude = city_data.get('longitude')

        points = await  _get_pickup_points(latitude, longitude, search_radius, client, auth_headers)
        filtered_points = get_filtered_russian_post_points_by_exact_city(points, city_data)
        
        print("-- All post points (qty):", len(points))
        print("-- Filtered post points (qty):", len(filtered_points))

        if not filtered_points:
            return {
                "status": "business_error",
                "error_code": "NO_POINTS_IN_REGION",
                "message": "В данном городе нет отделений Почты России"
            }
        
        # 2 - get delivery details
        index_to = city_data.get('postal_code')
        details = await _get_delivery_details(index_from, index_to, order_dimensions, order_price, client, auth_headers)
        
        print("-- Post delivery details:", details)

        if not details:
            return {
                "status": "tech_error",
                "error_code": "PRICE_CALCULATION_FAILED",
                "message": "Не удалось рассчитать стоимость доставки у Почты России."
            }
        
        delivery_days = format_delivery_days(details.get('delivery-days'))
        price = details.get('price')

        return {
            "status": "success",
            "error_code": None,
            "name": "Почта России",
            "points": filtered_points,
            "delivery_days": delivery_days,
            "price": price
        }
    
    except Exception as e:
        print(f"Критическая ошибка при запросе к Почте России: {e}")
        return {
            "status": "tech_error",
            "error_code": "POST_API_DOWN",
            "message": "Сервер службы доставки Почты России временно недоступен.",
            "points": []
        }
    
async def _get_pickup_points(latitude, longitude, search_radius, client, headers):
    url = current_app.config.get('RUSSIAN_POST', {}).get('URL_POINTS_LIST')
    query_params = {
        "latitude": latitude,
        "longitude": longitude,
        "search-radius": search_radius,
        "top": 1000,
        "filter": "ALL"
    }

    response = await client.get(
        url, 
        params=query_params,
        headers=headers, 
        timeout=5
    )

    response.raise_for_status()
    data = response.json()

    if not data:
        return None
    
    formatted_points = []
    for point in data:
        settlement = point.get('settlement') or ""
        address_source = point.get('address-source') or ""
        postal_code = point.get('postal-code') or ""
        formatted_points.append({
            "id": point.get('postal-code'),
            "address": f"{postal_code} {settlement} {address_source}".strip(),
            "settlement": settlement,
            "type-code": point.get('type-code')
        })

    return formatted_points

async def _get_delivery_details(index_from, index_to, order_dimensions, order_price, client, headers):
    url = current_app.config.get('RUSSIAN_POST', {}).get('URL_PRICING_CALCULATOR')

    # 1 - Divide into mini-boxes (20 kg)
    total_weight = order_dimensions.get('total_weight')
    number_of_places = math.ceil(total_weight / ORDER_WEIGHT_LIMIT)
    average_weight = math.ceil(total_weight / number_of_places)

    # 2 - Calculate shared declared value
    order_price_kopecks = order_price * 100
    shared_declared_value = math.ceil(order_price_kopecks / number_of_places)

    # 3 - Calculate side size
    big_cube_side = order_dimensions['cubic_sum_of_sides'] / 3
    if number_of_places > 1:
        avg_side = max(10, math.ceil(big_cube_side / math.pow(number_of_places, 1/3)))
    else:
        avg_side = max(10, math.ceil(big_cube_side))

    payload = {
        "index-from": index_from,
        "index-to": index_to,
        "mail-category": "WITH_DECLARED_VALUE",
        "mail-type": "ONLINE_PARCEL",
        "payment-method": "CASHLESS",
        "declared-value": shared_declared_value,
        "mass": average_weight,
        "dimension": {
            "height": avg_side,
            "length": avg_side,
            "width": avg_side
        }
    }

    response = await client.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()

    price = math.ceil((data.get('total-rate') + data.get('total-vat'))* number_of_places / 100) 

    return {
        "delivery-days": data.get('delivery-time').get('max-days'),
        "price": price
    }