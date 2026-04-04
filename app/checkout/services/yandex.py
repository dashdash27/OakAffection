import requests
import re
import math
from flask import current_app

yandex_session = requests.Session()

def get_yandex_delivery_session():
    if 'Authorization' not in yandex_session.headers:
        api_token = current_app.config.get('YANDEX_DELIVERY', {}).get('API_TOKEN')
        yandex_session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_token}"
        })
    return yandex_session


def get_yandex_delivery_info(city_data):
    source_point_id = current_app.config.get('YANDEX_DELIVERY', {}).get('SOURCE_PVZ_ID')

    try:
        geo_id = _detect_geo_id(city_data)
        
        if not geo_id:
            return None
        
        points = _get_pickup_points(geo_id)

        if not points:
            return None

        details = _get_delivery_details(source_point_id, points[0].get('id'))
        delivery_days = details.get('delivery_days')
        price = details.get('price')

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

def _detect_geo_id(city_data):
    url = current_app.config.get('YANDEX_DELIVERY', {}).get('URL_GEO_ID')
    payload = {
        "location": city_data.get('value')
    }

    session = get_yandex_delivery_session()
    response = session.post(url, json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()
    variants = data.get('variants', [])

    if not variants:
        return None
    
    first_variant = variants[0]
    return first_variant.get('geo_id')
    
def _get_pickup_points(geo_id):
    url = current_app.config.get('YANDEX_DELIVERY', {}).get('URL_POINTS_LIST')
    payload = {
        "geo_id": geo_id
    }

    session = get_yandex_delivery_session()
    response = session.post(url, json=payload, timeout=5)
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


def _get_delivery_details(source_point_id, destination_point_id):
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

    session = get_yandex_delivery_session()
    response = session.post(url, json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()

    delivery_days = data.get('delivery_days')
    price = data.get('pricing_total')

    print(delivery_days, price)

    return {
        "delivery_days": delivery_days,
        "price": price
    }
