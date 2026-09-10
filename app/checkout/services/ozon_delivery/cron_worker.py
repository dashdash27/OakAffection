from app.logger import logger
from app.checkout.services.ozon_delivery.auth import get_valid_access_token_sync
from app.checkout.services.ozon_delivery.utils import extract_city_context
from app.checkout.services.dadata import get_cities_fias

import sqlite3
import requests
import os
import time
from flask import current_app


session = requests.Session()

def init_db(db_path: str):
    logger.info("Инициализация базы данных SQLite для Ozon Delivery API...")

    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Создана директория для БД: {db_dir}")

    with sqlite3.connect(db_path, timeout=30.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()

        # Cash DaData
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dadata_cities_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_context TEXT UNIQUE,
                fias_id TEXT
            )
        """)

        # Tokens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                token TEXT,
                expires_at INTEGER
            )
        """)

        # Ozon Points
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

        # Methods
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
    logger.info("[Ozon Delivery API] Запрос списка всех ID ПВЗ...")

    url = ozon_delivery_cfg.get("URL_POINTS_LIST")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    all_points = []
    current_cursor = None
    page_counter = 1

    logger.info("[Ozon Delivery API] Начинаем потоковый сбор ID ПВЗ через курсор...")

    while True:
        payload = {
            "pagination": {
                "cursor": current_cursor,
                "limit": 100
            }
        }

        try:
            logger.info(f"[Ozon Delivery API] Запрос страницы {page_counter} (cursor: {current_cursor})...")

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            points = data.get("delivery_points", [])
            all_points.extend(points)

            logger.info(f"[Ozon Delivery API] Страница {page_counter} успешно обработана. Получено точек: {len(points)}.")

            next_cursor = data.get("next_cursor")

            if not next_cursor or next_cursor == current_cursor:
                logger.info(f"[Ozon Delivery API] Курсор пуст или завершен. Всего найдено ПВЗ: {len(all_points)}")
                break

            current_cursor = next_cursor
            page_counter += 1

            time.sleep(0.2)

        except requests.exceptions.RequestException as e:
            # Если сеть моргнет на середине пути, крон не упадет
            logger.error(f"[Ozon Delivery API] Сетевая ошибка на странице {page_counter}: {e}")
            
            # Если мы уже успели выкачать часть данных, возвращаем их, чтобы конвейер продолжил работу
            if all_points:
                logger.warning(f"[Ozon Delivery API] Возвращаем частично собранные данные ({len(all_points)} ПВЗ) из-за ошибки.")
                return all_points

            return []

    return all_points


def fetch_point_details_chunk(ozon_delivery_cfg: dict, access_token: str, point_ids: list[int]) -> list[dict]:
    """Отправляет массив из ID ПВЗ и получает детали о каждом ПВЗ"""

    url = ozon_delivery_cfg.get("URL_POINTS_INFO")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    detailed_points = []
    chunk_size = 100
    total_ids = len(point_ids)

    logger.info(f"[Ozon Delivery API] Начинаем сбор деталей для {total_ids} ПВЗ...")

    for i in range(0, total_ids, chunk_size):
        chunk = point_ids[i:i + chunk_size]
        chunk_number = (i // chunk_size) + 1
        total_chunks = (total_ids + chunk_size - 1) // chunk_size

        payload = {
            "delivery_point_ids": chunk
        }

        max_retries = 3
        for retry in range(max_retries):
            try:
                logger.info(f"[Ozon Delivery API]: Запрос чанка {chunk_number}/{total_chunks}...")
                
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()

                # Извлекаем список точек из ответа
                points_chunk = data.get("delivery_points", [])
                detailed_points.extend(points_chunk)
                
                break

            except requests.exceptions.RequestException as e:
                logger.warning(f"[Ozon Delivery API] Ошибка чанка {chunk_number} (Попытка {retry + 1}/{max_retries}): {e}")
                
                if retry < max_retries - 1:
                    time.sleep(2)  # Ждем 2 секунды перед повторной попыткой
                else:
                    # Если все 3 попытки провалились — пропускаем этот чанк, чтобы не ронять весь Крон
                    logger.warning(f"[Ozon Delivery API] Чанк {chunk_number} окончательно провален после {max_retries} попыток. Пропускаем.")

        # Шаг 3: Обязательная микро-пауза между чанками для защиты от Rate Limit Ozon (ошибка 429)
        time.sleep(0.3)

    logger.info(f"[Ozon Delivery API] Сбор деталей завершен. Успешно получено: {len(detailed_points)} из {total_ids} ПВЗ.")
    return detailed_points


def save_points_and_methods_to_db(db_path: str, detailed_points: list, point_methods_map: dict, city_to_fias_map: dict):
    """
        Сохраняет ПВЗ и их методы доставки в SQLite.
        Очищает закрывшиеся точки.
    """
    logger.info(f"[Cron Ozon Delivery] Сохранение информации о полученных ПВЗ Ozon в базу данных SQLite...")

    # 1. Подготовка данных
    points_data = []
    methods_data = []

    for p in detailed_points:
        ozon_point_id = p.get("delivery_point_id")
        if not ozon_point_id:
            continue
            
        city_ctx = extract_city_context(p.get("full_address", ""))
        fias_id = city_to_fias_map.get(city_ctx)
        
        # Извлекаем координаты
        coords = p.get("coordinates") or {}
        latitude = coords.get("latitude")
        longitude = coords.get("longitude")

        # Набор данных для таблицы ozon_points
        points_data.append((
            ozon_point_id,
            p.get("name", ""),
            p.get("full_address", ""),
            latitude,
            longitude,
            fias_id
        ))
        
        # Добавляем методы
        methods = point_methods_map.get(ozon_point_id, [])
        for m_id in methods:
            methods_data.append((ozon_point_id, m_id))

    logger.info(f"[Cron Ozon Delivery] Подготовлено к записи: {len(points_data)} точек и {len(methods_data)} методов доставки.")

    # 2. Запись в БД
    with sqlite3.connect(db_path, timeout=30.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()

        batch_size = 1000 # порции

        # 2.1. Создаем временную таблицу для актуальных ID точек
        cursor.execute("CREATE TEMP TABLE IF NOT EXISTS fresh_point_ids (ozon_point_id INTEGER PRIMARY KEY);")

        # наполняем ее актуальными ID из Ozon
        fresh_ids_tuple = [(row[0],) for row in points_data]
        for i in range(0, len(fresh_ids_tuple), batch_size):
            # добавит новый индекс или пропустит, если он уже есть (работает порционно по batch)
            cursor.executemany("INSERT OR IGNORE INTO fresh_point_ids (ozon_point_id) VALUES (?);", fresh_ids_tuple[i:i + batch_size])

        # 2.2. Порционно обновляем инфу о ПВЗ в главной таблице (добавит или обновит)
        logger.info(f"[Cron Ozon Delivery] Запись {len(points_data)} ПВЗ в базу...")
        for i in range(0, len(points_data), batch_size):
            cursor.executemany("""
                INSERT INTO ozon_points (ozon_point_id, name_raw, address, latitude, longitude, fias_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(ozon_point_id) DO UPDATE SET
                    name_raw=excluded.name_raw,
                    address=excluded.address,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    fias_id=excluded.fias_id;
            """, points_data[i:i + batch_size])

        # 2.3. Полностью очищаем таблицу методов доставки
        cursor.execute("DELETE FROM ozon_point_shipment_methods;")

        # Добавляем новые актуальные методы доставки
        logger.info(f"[Cron Ozon Delivery] Запись {len(methods_data)} методов доставки в SQLite...")
        for i in range(0, len(methods_data), batch_size):
            cursor.executemany("""
                INSERT INTO ozon_point_shipment_methods (ozon_point_id, shipment_method_id)
                VALUES (?, ?)
            """, methods_data[i:i + batch_size])

        # 2.4 Автоматическое удаление закрывшихся точек
        cursor.execute("""
            DELETE FROM ozon_points 
            WHERE ozon_point_id NOT IN (SELECT ozon_point_id FROM fresh_point_ids);
        """)

        cursor.execute("DROP TABLE fresh_point_ids;")

        conn.commit()

        logger.info("[Cron Ozon Delivery] Все данные успешно зафиксированы в SQLite.")

        

def run_full_pickup_points_sync():
    """
        Главная управляющая функция конвейера ПВЗ Ozon.
        Вызывается Кроном из tasks/sync_ozon_pickup_points.py в контексте Flask.
    """
    logger.info("[Cron Ozon Delivery] Старт еженедельной синхронизации базы ПВЗ Ozon...")

    ozon_delivery_cfg = current_app.config.get("OZON_DELIVERY")
    db_path = ozon_delivery_cfg.get("DB_PATH")

    if not db_path:
        logger.error("[Cron Ozon Delivery] Критическая ошибка: Не задан путь DB_PATH в конфигурации OZON_DELIVERY!")
        return

    init_db(db_path)

    try:
        # 1. Get access token
        access_token = get_valid_access_token_sync(ozon_delivery_cfg)
        logger.info("[Cron Ozon Delivery] Токен Ozon API успешно верифицирован.")

        # 2. Get raw points
        raw_points = fetch_all_ozon_point_ids(ozon_delivery_cfg, access_token)
        if not raw_points:
            logger.warning("[Cron Ozon Delivery] Базовые ID ПВЗ не получены. Выходим.")
            return
        logger.info("[Cron Ozon Delivery] Базовые ID ПВЗ успешно получены.")

        # 3. Save points methods
        point_methods_map = {p["delivery_point_id"]: p.get("shipment_method_ids", []) for p in raw_points}
        point_ids = list(point_methods_map.keys())

        # 4. Get detailed points
        detailed_points = fetch_point_details_chunk(ozon_delivery_cfg, access_token, point_ids)
        if not detailed_points:
            logger.warning("[Cron Ozon Delivery] Детализация ПВЗ пуста. Выходим.")
            return
        logger.info(f"[Cron Ozon Delivery] Детали ПВЗ успешно получены.")

        # 5. Get unique cities for dadata
        unique_cities = set()    
        for p in detailed_points:
            city_ctx = extract_city_context(p.get("full_address", ""))
            if city_ctx:
                unique_cities.add(city_ctx)
        logger.info(f"[Cron Ozon Delivery] Найдено {len(unique_cities)} уникальных населенных пунктов.")

        # 6. Get fias_id for cities
        city_to_fias_map = get_cities_fias(unique_cities, db_path)
        if city_to_fias_map == {}:
            logger.warning("[Cron Ozon Delivery] Не получены FIAS для населенных пунктов. Выходим.")
            return
        logger.info(f"[Cron Ozon Delivery] FIAS для населенных пунктов успешно получены.")

        # 7. Save to DB
        save_points_and_methods_to_db(db_path, detailed_points, point_methods_map, city_to_fias_map)

        logger.info("[Cron Ozon Delivery] Фоновая задача синхронизации успешно завершена!")
            
        
    except Exception as e:
        logger.exception(f"[Cron Ozon] КРИТИЧЕСКАЯ ОШИБКА в процессе работы конвейера Ozon ПВЗ: {e}")
    