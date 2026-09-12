from app.logger import logger

import requests
from flask import current_app
import time
import sqlite3

dadata_session = requests.Session()

def get_dadata_session():
    api_key = current_app.config.get('DADATA', {}).get('API_KEY')
    
    dadata_session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {api_key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    return dadata_session

def format_suggestion(s):
    data = s.get('data', {})
    return {
        "value": s.get('value'),
        "unrestricted_value": s.get('unrestricted_value'),
        "region_fias_id": data.get('region_fias_id'),
        "fias_level": data.get('fias_level'),
        "fias_id": data.get("settlement_fias_id") or data.get("city_fias_id"),
        "latitude": data.get('geo_lat'),
        "longitude": data.get('geo_lon'),
        "postal_code": data.get('postal_code') or "",
        "settlement": data.get('city') or data.get('settlement') or ""
    }

def get_city_suggestions(query): 
    url = current_app.config.get('DADATA', {}).get('URL_ADDRESS_SUGGESTIONS')

    data = {
        "query": query, 
        "from_bound": {"value": "city"}, 
        "to_bound": {"value": "settlement"}
    }
    
    try:
        session = get_dadata_session()
        response = session.post(url, json=data, timeout=5)
        response.raise_for_status() 

        suggestions = response.json().get('suggestions', [])

        return [format_suggestion(s) for s in suggestions]

    except requests.exceptions.RequestException:
        logger.error(f"Сеть или API DaData вернули ошибку для запроса: {query}")
        return None
    except Exception:
        logger.exception("Критическая авария при обработке подсказок городов")
        return None

def get_cities_fias(unique_cities: set[str], db_path: str) -> dict[str, str]:
    """
        Собирает fias_id из списка уникальных населенных пунктов
        Сначала проверяет локальную таблицу dadata_cities_cache,
        а в DaData идет только за неизвестными ранее городам.
    """
    url = current_app.config.get('DADATA', {}).get('URL_ADDRESS_SUGGESTIONS')
    
    if not url:
        logger.error("[Cron DaData] URL_ADDRESS_SUGGESTIONS не найден в конфигурации DADATA!")
        return {}

    city_to_fias = {}
    logger.info("[DaData] Запрос в кэш БД SQLite для получения FIAS...")

    # Пытаемся получить fias из локальной БД SQLite
    try:
        with sqlite3.connect(db_path, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT city_context, fias_id FROM dadata_cities_cache")
            rows = cursor.fetchall()
            for context, fias in rows:
                if fias:  # Сохраняем только валидные fias_id
                    city_to_fias[context] = fias
        logger.info(f"[SQLite Cache] В локальной базе найдено {len(city_to_fias)} FIAS населенных пунков.")
    except Exception as e:
        logger.error(f"[SQLite Cache] Ошибка при чтении кэша городов: {e}")

    # Вычисляем разницу (что нужно реально спросить у Dadata)
    cities_to_request_dadata = unique_cities - set(city_to_fias.keys())
    if not cities_to_request_dadata:
        logger.info("[DaData]: Все города взяты из локального кэша. Сетевые запросы не требуются!")
        return city_to_fias

    # Запрос к Dadata
    logger.info(f"[DaData] Новых городов для отправки в API DaData: {len(cities_to_request_dadata)}")

    new_cached_entries = []
    requested_count = 0
    MAX_DAILY_LIMIT = 9500

    try:
        session = get_dadata_session()
        
        for city_str in cities_to_request_dadata:
            if not city_str:
                continue

            if requested_count >= MAX_DAILY_LIMIT:
                logger.warning(
                    f"[DaData] Достигнут внутренний лимит безопасности в {MAX_DAILY_LIMIT} запросов за запуск! "
                    f"Оставшиеся города переносятся на следующий запуск Крона."
                )
                break
                
            data = {
                "query": city_str, 
                "count": 1,
                "from_bound": {"value": "city"}, 
                "to_bound": {"value": "settlement"}
            }
            
            try:
                response = session.post(url, json=data, timeout=5)
                response.raise_for_status() 

                suggestions = response.json().get('suggestions', [])
                if suggestions:
                    match_data = suggestions[0].get("data", {})
                    
                    fias_id = match_data.get("settlement_fias_id") or match_data.get("city_fias_id")
                    if fias_id:
                        city_to_fias[city_str] = fias_id

                new_cached_entries.append((city_str, fias_id))

                requested_count += 1
                if requested_count % 500 == 0:
                    logger.info(f"[DaData] Обработано {requested_count} новых городов...")

                time.sleep(0.05)

            except Exception as e:
                logger.error(f"[DaData]: Ошибка при обработке города '{city_str}': {e}")
                if "403" in str(e):
                    logger.critical("[DaData API]: Бесплатный дневной лимит DaData (10к) исчерпан!")
                    break

    except Exception as e:
        logger.exception(f"[DaData]: Критическая авария при инициализации сессии DaData: {e}")

    # Сохраняем новые распознанные города
    if new_cached_entries:
        try:
            with sqlite3.connect(db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.executemany("""
                    INSERT OR IGNORE INTO dadata_cities_cache (city_context, fias_id) 
                    VALUES (?, ?)
                """, new_cached_entries)
                conn.commit()
            logger.info(f"[SQLite Cache] Локальный кэш успешно пополнен на {len(new_cached_entries)} записей.")
        except Exception as e:
            logger.error(f"[SQLite Cache] Ошибка при сохранении новых городов в кэш: {e}")

    logger.info(f"[DaData] Финал. Добавлено новых FIAS: {len(new_cached_entries)}.")
    return city_to_fias