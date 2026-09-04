from app.logger import logger
from app.checkout.services.ozon_delivery.auth import get_valid_access_token_async
from app.checkout.utils import format_delivery_days, normalize_and_ceil_price, generate_jwt_delivery_token

import sqlite3

async def get_ozon_delivery_info(city_data, order_dimensions, order_price, client, ozon_delivery_cfg: dict):
    logger.debug(f"Получение информации о доставке Ozon Delivery для города: {city_data.get('value')}")

    try:
        fias_id = city_data.get('fias_id')
        # TODO: метод доставки в зависимости от веса подгружать
        shipment_method_id = 1

        # 1. Get Points by fias_id and shipment_method
        points = _get_pickup_points(fias_id, shipment_method_id, ozon_delivery_cfg)
        if not points:
            logger.warning(f"Ozon Delivery: Не удалось получить ПВЗ для города: {city_data.get('value')}")
            return {
                "status": "business_error",
                "error_code": "NO_POINTS_IN_REGION",
                "message": "В данном городе нет ПВЗ Ozon"
            }

        # 2. Get delivery details
        # TODO: try для получения токена
        access_token = await get_valid_access_token_async(client, ozon_delivery_cfg)
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        details = None
        ozon_point_id_to = points[0].get('id')

        details = await _get_delivery_details(ozon_point_id_to, order_dimensions, order_price, shipment_method_id, client, auth_headers, ozon_delivery_cfg)
        if not details or not details.get('price'):
            logger.warning(f"Ozon Delivery: Не удалось рассчитать цену для города {city_data.get('value')}")
            return {
                "status": "tech_error",
                "error_code": "PRICE_CALCULATION_FAILED",
                "message": "Не удалось рассчитать стоимость доставки у Ozon."
            }

        delivery_days = format_delivery_days(details.get('delivery_days'))
        clean_price = normalize_and_ceil_price(details.get('price'))

        return {
                "status": "success",
                "error_code": None,
                "name": "Ozon",
                "service": "ozon",
                "points": points,
                "delivery_days": delivery_days,
                "price": clean_price, 
                "delivery_token": "ddd"
            }
        
        
    except Exception as e:
        logger.exception(f"Критическая ошибка во время интеграции с Ozon Delivery")
        return {
            "status": "tech_error",
            "error_code": "OZON_DELIVERY_API_DOWN",
            "message": "Сервер службы доставки Ozon Delivery временно недоступен."
        }


def _get_pickup_points(fias_id, shipment_method_id, ozon_delivery_cfg: dict):

    db_path = ozon_delivery_cfg.get('DB_PATH')
    conn = sqlite3.connect(db_path, timeout=3.0)

    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        
        conn.row_factory = sqlite3.Row 
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.ozon_point_id, p.name_raw, p.address, p.latitude, p.longitude
            FROM ozon_points p
            INNER JOIN ozon_point_shipment_methods m ON p.ozon_point_id = m.ozon_point_id
            WHERE p.fias_id = ? AND m.shipment_method_id = ?
        """, (fias_id, shipment_method_id))
        
        rows = cursor.fetchall()

        pickup_points = []
        for row in rows:
            pickup_points.append({
                "id": str(row["ozon_point_id"]),
                "name": row["name_raw"] or "ПВЗ Ozon",
                "address": row["address"]
            })
            
        return pickup_points
    
    except Exception as e:
        logger.error(f"[Ozon Delivery] Ошибка при чтении ПВЗ из SQLite: {e}")
        return None
    
    finally:
        conn.close()

async def _get_delivery_details(ozon_point_id_to, order_dimensions, order_price, shipment_method_id, client, headers, ozon_delivery_cfg: dict):
    url = ozon_delivery_cfg.get('URL_PRICING_CALCULATOR')

    payload = {
        "recipient": {
            "phone_number": "+79991234567"
        },
        "postings": [
            {
            "request_id": 105,
            "shipment_method_id": shipment_method_id,
            "cutoff_at": "2026-09-16T12:00:00Z",
            "declared_value": {
                "amount": str(order_price),
                "currency_code": "RUB"
            },
            "dimensions": {
                "weight_g": order_dimensions.get('total_weight'),
                "length_mm": 200,
                "width_mm": 150,
                "height_mm": 100
            }
            }
        ],
        "delivery": {
            "delivery_point": {
                "delivery_point_id": ozon_point_id_to
            }
        }
    }

    response = await client.post(url, json=payload, headers=headers, timeout=5, follow_redirects=True)
    response.raise_for_status()
    data = response.json()

    delivery_days = data.get('results')[0].get('posting').get('estimated_delivery_days')
    price = data.get('results')[0].get('posting').get('estimated_delivery_cost').get('amount')

    return {
        "delivery_days": delivery_days,
        "price": price
    }