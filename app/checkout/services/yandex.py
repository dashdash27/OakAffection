import re
import asyncio
import math
from flask import current_app

from ..utils import format_delivery_days

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


async def get_yandex_delivery_info(city_data, client):
    api_token = current_app.config.get('YANDEX_DELIVERY', {}).get('API_TOKEN')
    source_point_id = current_app.config.get('YANDEX_DELIVERY', {}).get('SOURCE_PVZ_ID')
    auth_headers = {"Authorization": f"Bearer {api_token}"}

    try:
        geo_id = await _detect_geo_id(city_data, client, auth_headers)
        
        if not geo_id:
            return None
        
        points =await  _get_pickup_points(geo_id, client, auth_headers)

        if not points:
            return None

        details = await  _get_delivery_details(source_point_id, points[0].get('id'), client, auth_headers)
        delivery_days = format_delivery_days(details.get('delivery_days'))
        price = details.get('price')

        if not price:
            return None

        # очищаем цену
        clean_price = re.sub(r'[^\d.,]', '', str(price))
        clean_price = clean_price.replace(',', '.')
        clean_price = math.ceil(float(clean_price))
        
        return {
            "geo_id": geo_id,
            "points": points,
            "delivery_days": delivery_days,
            "price": clean_price
        }
    
    except:
        print("Ошибка при запросе к Yandex")
        return None

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
        })
        
    return formatted_points


async def _get_delivery_details(source_point_id, destination_point_id, client, headers):
    url = current_app.config.get('YANDEX_DELIVERY', {}).get('URL_PRICING_CALCULATOR')
    payload = {
        "destination": {
            "platform_station_id": destination_point_id
        },
        "source": {
            "platform_station_id": source_point_id
        },
        "tariff": "self_pickup" ,
        "total_weight": 4000
    }
    
    response = await client.post(url, json=payload, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()

    delivery_days = data.get('delivery_days')
    price = data.get('pricing_total')

    print(delivery_days, price)

    return {
        "delivery_days": delivery_days,
        "price": price
    }
