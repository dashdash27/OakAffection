import requests
import random
from config import Config

YANDEX_API_KEY = Config.YANDEX_API_KEY;

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {YANDEX_API_KEY}"
})

def get_yandex_delivery_info(city_data):
    source_point_id = "e1139f6d-e34f-47a9-a55f-31f032a861a6"

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
        
        return {
            "geo_id": geo_id,
            "points": points,
            "delivery_days": delivery_days,
            "price": price
        }
    
    except:
        print("Ошибка при запросе к Yandex")
        return None

def _get_delivery_details(source_point_id, destination_point_id):
    url = "https://b2b.taxi.tst.yandex.net/api/b2b/platform/pricing-calculator"
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

    response = session.post(url, json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()

    delivery_days = data.get('delivery_days')
    price = data.get('pricing_total')

    return {
        "delivery_days": delivery_days,
        "price": price
    }

def _detect_geo_id(city_data):
    url = "https://b2b.taxi.tst.yandex.net/api/b2b/platform/location/detect"
    payload = {
        "location": city_data.get('value')
    }
    response = session.post(url, json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()
    variants = data.get('variants', [])

    if not variants:
        return None
    
    first_variant = variants[0]
    return first_variant.get('geo_id')
    
def _get_pickup_points(geo_id):
    url = "https://b2b.taxi.tst.yandex.net/api/b2b/platform/pickup-points/list"
    payload = {
        "geo_id": geo_id
    }

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