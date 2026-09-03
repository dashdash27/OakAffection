from app.logger import logger
from app.checkout.services.ozon_delivery.auth import get_valid_access_token_sync
from app.checkout.services.ozon_delivery.utils import extract_city_context
from app.checkout.services.dadata import get_cities_fias

import sqlite3
import requests
import os
from flask import current_app


session = requests.Session()

def init_db(db_path: str):
    logger.info("Инициализация базы данных SQLite для Ozon Delivery API...")

    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Создана директория для БД: {db_dir}")

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                token TEXT,
                expires_at INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ozon_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ozon_point_id BIGINT UNIQUE,
                name_raw TEXT,
                address TEXT,
                latitude FLOAT,
                longitude FLOAT,
                fias_id TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ozon_point_shipment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ozon_point_id BIGINT,
                shipment_method_id BIGINT
            )
        """)
        
        # Индексы для быстрого JOIN-поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ozon_points_fias ON ozon_points(fias_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_methods_point_id ON ozon_point_shipment_methods(ozon_point_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_methods_shipment_id ON ozon_point_shipment_methods(shipment_method_id);")
        conn.commit()

def fetch_all_ozon_point_ids(ozon_delivery_cfg: dict, access_token: str) -> list[dict]:
    """
    Скачивает порциями ID всех ПВЗ и поддерживаемые методы доставки.
    Использует синхронный requests и пагинацию Ozon API через указатель (cursor). Для Cron.
    """
    logger.info("[Ozon Delivery API]: Запрос списка всех ID ПВЗ...")

    url = ozon_delivery_cfg.get("URL_POINTS_LIST")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "pagination": {
            "cursor": None,
            "limit": 2
        }
    }

    # TODO: сделать циклом и по указателю

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Забираем сырой список точек из JSON
        points = data.get("delivery_points", [])
        
        logger.info(f"[Ozon Delivery API]: Из ответа API Ozon успешно получено ровно {len(points)} ПВЗ. {points}")
        return points
        
    except Exception as e:
        logger.error(f"Ozon Delivery API [Test]: Ошибка при запросе к Ozon API: {e}")
        raise e

    all_points = []
    cursor = None
    has_next = True

    while has_next:
        payload = {"limit": 100}
        if cursor:
            payload["cursor"] = cursor
            
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # По структуре Ozon: "delivery_points": [{"delivery_point_id": 5750, "shipment_method_ids": [...]}]
            points = data.get("delivery_points", [])
            all_points.extend(points)
            
            # Извлекаем указатель на следующую порцию данных
            cursor = data.get("next_cursor")
            has_next = bool(cursor)
            
        except Exception as e:
            logger.error(f"Ozon Delivery API [Cron]: Ошибка при пагинации ID ПВЗ на курсоре {cursor}: {e}")
            raise e  # Прерываем Крон, если Озон недоступен, чтобы не побить старую базу данных пустотой
        
    logger.info(f"Ozon Delivery API: Успешно собрано {len(all_points)} ID пунктов выдачи.")
    return all_points

def fetch_point_details_chunk(ozon_delivery_cfg: dict, access_token: str, point_ids: list[int]) -> list[dict]:
    """
    Отправляет массив из ID ПВЗ и получает детали о каждом ПВЗ
    """
    logger.info(f"[Ozon Delivery API]: Запрос деталей для {len(point_ids)} ПВЗ...")

    url = ozon_delivery_cfg.get("URL_POINTS_INFO")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {"delivery_point_ids": point_ids}

    # TODO: тут разбить на цикл по 100 шт

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        detailed_points = data.get("delivery_points", [])
        return detailed_points
    
    except Exception as e:
        logger.error(f"[Ozon Delivery API]: Ошибка при запросе деталей ПВЗ: {e}")
        raise e


def save_points_and_methods_to_db(db_path: str, detailed_points: list, point_methods_map: dict, city_to_fias_map: dict):
    """Сохраняет ПВЗ и их методы доставки в SQLite одной быстрой транзакцией."""
    logger.info(f"[Cron Ozon Delivery] Запись {len(detailed_points)} точек в базу данных...")

    conn = sqlite3.connect(db_path, timeout=10.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        
        # Очищаем старые методы, так как связи могут меняться (точки заменяются по UNIQUE)
        cursor.execute("DELETE FROM ozon_point_shipment_methods;")
        
        points_data = []
        methods_data = []
        
        for p in detailed_points:
            ozon_point_id = p.get("delivery_point_id") # подставьте ваш точный ключ из API
            if not ozon_point_id:
                continue
                
            city_ctx = extract_city_context(p.get("full_address", ""))
            fias_id = city_to_fias_map.get(city_ctx)
            
            # Данные для таблицы ozon_points
            coords = p.get("coordinates") or {}
            latitude = coords.get("latitude")
            longitude = coords.get("longitude")

            points_data.append((
                ozon_point_id,
                p.get("full_address", ""),
                p.get("full_address", ""),
                latitude,
                longitude,
                fias_id
            ))
            
            # Данные для связующей таблицы методов доставки
            methods = point_methods_map.get(ozon_point_id, [])
            for m_id in methods:
                methods_data.append((ozon_point_id, m_id))
                
        # Массовая вставка (executemany)
        cursor.executemany("""
            INSERT INTO ozon_points (ozon_point_id, name_raw, address, latitude, longitude, fias_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(ozon_point_id) DO UPDATE SET
                name_raw=excluded.name_raw,
                address=excluded.address,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                fias_id=excluded.fias_id
        """, points_data)
        
        cursor.executemany("""
            INSERT INTO ozon_point_shipment_methods (ozon_point_id, shipment_method_id)
            VALUES (?, ?)
        """, methods_data)

        # Удаляем те точки, которые уже не актуальны
        fresh_ids = [row[0] for row in points_data]
        if fresh_ids:
            placeholders = ",".join("?" for _ in fresh_ids)
            cursor.execute(f"""
                DELETE FROM ozon_points 
                WHERE ozon_point_id NOT IN ({placeholders})
            """, fresh_ids)
            
            logger.info(f"[Cron Ozon Delivery] Очистка завершена. Удалены закрывшиеся точки.")
        
        conn.commit()
        logger.info("[Cron Ozon Delivery] Все данные успешно зафиксированы в SQLite.")
    except Exception as e:
        logger.error(f"[Cron Ozon Delivery] Ошибка при сохранении данных в БД: {e}")
        raise
    finally:
        conn.close()

def run_full_pickup_points_sync():
    """
    Главная управляющая функция конвейера ПВЗ Ozon.
    Вызывается Кроном из tasks/sync_ozon_pickup_points.py в контексте Flask.
    """
    logger.info("[Cron Ozon Delivery]: Старт еженедельной синхронизации базы ПВЗ Ozon...")

    ozon_delivery_cfg = current_app.config.get("OZON_DELIVERY")
    db_path = ozon_delivery_cfg.get("DB_PATH")

    if not db_path:
        logger.error("[Cron Ozon Delivery]: Критическая ошибка: Не задан путь DB_PATH в конфигурации OZON_DELIVERY!")
        return

    init_db(db_path)

    try:
        # 1. Get access token
        access_token = get_valid_access_token_sync(ozon_delivery_cfg)
        logger.info("[Cron Ozon Delivery]: Токен Ozon API успешно верифицирован.")

        # 2. Get raw points
        raw_points = fetch_all_ozon_point_ids(ozon_delivery_cfg, access_token)
        if not raw_points:
            logger.warning("[Cron Ozon Delivery]: Базовые ID ПВЗ не получены. Выходим.")
            return
        logger.info("[Cron Ozon Delivery]: Базовые ID ПВЗ успешно получены.")

        # 3. Save points methods
        point_methods_map = {p["delivery_point_id"]: p.get("shipment_method_ids", []) for p in raw_points}
        point_ids = list(point_methods_map.keys())

        # 4. Get detailed points
        detailed_points = fetch_point_details_chunk(ozon_delivery_cfg, access_token, point_ids)
        if not detailed_points:
            logger.warning("[Cron Ozon Delivery]: Детализация ПВЗ пуста. Выходим.")
            return
        logger.info(f"[Cron Ozon Delivery]: Детали для {len(detailed_points)} ПВЗ успешно получены.")

        # 5. Get unique cities for dadata
        unique_cities = set()    
        for p in detailed_points:
            logger.debug(f"Address: {p.get("full_address", "")}")
            city_ctx = extract_city_context(p.get("full_address", ""))
            if city_ctx:
                unique_cities.add(city_ctx)
        logger.info(f"[Cron Ozon Delivery]: Найдено {len(unique_cities)} уникальных населенных пунктов.")

        # 6. Get fias_id for cities
        city_to_fias_map = get_cities_fias(unique_cities)
        if city_to_fias_map == {}:
            logger.warning("[Cron Ozon Delivery]: Не получены fias_id для населенных пунктов. Выходим.")
            return
        logger.info(f"[Cron Ozon Delivery]: Успешно получены fias_id для населенных пунктов: {city_to_fias_map}")

        # 7. Save to DB
        save_points_and_methods_to_db(db_path, detailed_points, point_methods_map, city_to_fias_map)

        logger.info("[Cron Ozon Delivery]: Фоновая задача синхронизации успешно завершена!")
            
        
    except Exception as e:
        logger.exception(f"[Cron Ozon]: КРИТИЧЕСКАЯ ОШИБКА в процессе работы конвейера: {e}")
    