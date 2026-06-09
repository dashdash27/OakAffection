import re
import asyncio
import math
from flask import current_app
import json

from ..utils import format_delivery_days
from .yandex_delivery_utils import get_allowed_yandex_profiles, get_filtered_yandex_points

async def get_fake_delivery_info(city_data, client):
    """Имитация долгого запроса к Доставке"""
    print("Начинаю запрос к Доставке...")
    
    await asyncio.sleep(5) 
    
    print("Доставка ответила через 5 секунд!")
    
    return {
        "service": "yandex",
        "price": 500,
        "days": "2-3 дня",
        "status": "success"
    }


async def get_yandex_delivery_info(city_data, order_dimensions, client):
    api_token = current_app.config.get('YANDEX_DELIVERY', {}).get('API_TOKEN')
    source_point_id = current_app.config.get('YANDEX_DELIVERY', {}).get('SOURCE_PVZ_ID')
    auth_headers = {"Authorization": f"Bearer {api_token}"}

    print("Yandex delivery info request...")

    try:
        geo_id = await _detect_geo_id(city_data, client, auth_headers)
        
        if not geo_id:
            return {
                "status": "business_error",
                "error_code": "NO_REGION_ID",
                "message": "Не удалось определить geo_id для данного города."
            }
        
        print("-- Geo id:", geo_id)
        
        points = await  _get_pickup_points(geo_id, client, auth_headers)

        if not points:
            return {
                "status": "business_error",
                "error_code": "NO_POINTS_IN_REGION",
                "message": "В данном городе нет ПВЗ Яндекса"
            }
        
        # 1 - get allowed profiles to order
        allowed_profiles = get_allowed_yandex_profiles(order_dimensions, city_data.get('region_fias_id'))
        print("-- Allowed profiles:", allowed_profiles)

        # 2 - filter points by allowed profiles
        filtered_points = get_filtered_yandex_points(points, allowed_profiles)

        print("-- All yandex points (qty):", len(points))
        print("-- Filtered yandex points (qty):", len(filtered_points))
        
        if not filtered_points:
            return {
                "status": "business_error",
                "error_code": "OVERSIZE_OR_OVERWEIGHT",
                "message": "Заказ слишком тяжелый или объемный для ПВЗ в вашем регионе."
            }
        
        details = None
        
        for test_point in filtered_points[:3]:
            try:
                details = await _get_delivery_details(
                    source_point_id, 
                    test_point.get('id'),
                    order_dimensions, 
                    client, 
                    auth_headers
                )
                if details and details.get('price'):
                    break
            except Exception as calc_error:
                print(f"Точка ID {test_point.get('id')} не подошла для расчета цены: {calc_error}")
                continue

        if not details or not details.get('price'):
            return {
                "status": "tech_error",
                "error_code": "PRICE_CALCULATION_FAILED",
                "message": "Не удалось рассчитать стоимость доставки у Яндекса."
            }
        
        delivery_days = format_delivery_days(details.get('delivery_days'))
        price = details.get('price')

        # clear price
        clean_price = re.sub(r'[^\d.,]', '', str(price))
        clean_price = clean_price.replace(',', '.')
        clean_price = math.ceil(float(clean_price))

        print("-- Yandex delivery details:", json.dumps(details, indent=4))
        
        return {
            "status": "success",
            "error_code": None,
            "name": "Яндекс Доставка",
            "points": filtered_points,
            "delivery_days": delivery_days,
            "price": clean_price
        }
    
    except Exception as e:
        print(f"Критическая ошибка при запросе к Yandex: {e}")
        return {
            "status": "tech_error",
            "error_code": "YANDEX_API_DOWN",
            "message": "Сервер службы доставки Яндекса временно недоступен.",
            "points": []
        }

async def _detect_geo_id(city_data, client, headers):
    url = current_app.config.get('YANDEX_DELIVERY', {}).get('URL_GEO_ID')
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
    
async def _get_pickup_points(geo_id, client, headers):
    url = current_app.config.get('YANDEX_DELIVERY', {}).get('URL_POINTS_LIST')
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


async def _get_delivery_details(source_point_id, destination_point_id, order_dimensions, client, headers):
    url = current_app.config.get('YANDEX_DELIVERY', {}).get('URL_PRICING_CALCULATOR')

    SAFE_BOX_WEIGHT = 15000 
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