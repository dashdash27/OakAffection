from app.logger import logger

import requests
from flask import current_app
import time

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

def get_cities_fias(unique_cities: set[str]) -> dict[str, str]:
    """Собирает fias_id из списка уникальных населенных пунктов"""
    url = current_app.config.get('DADATA', {}).get('URL_ADDRESS_SUGGESTIONS')
    
    if not url:
        logger.error("[Cron DaData]: URL_ADDRESS_SUGGESTIONS не найден в конфигурации DADATA!")
        return {}

    city_to_fias = {}
    logger.info(f"[DaData]: Опрос подсказок для получения fias_id{len(unique_cities)} уникальных локаций...")

    try:
        session = get_dadata_session()
        
        for city_str in unique_cities:
            if not city_str:
                continue
                
            data = {
                "query": city_str, 
                "count": 1, # Нам нужен строго 1 самый точный результат
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
                
                time.sleep(0.05)

            except Exception as e:
                logger.error(f"[DaData]: Ошибка при обработке города '{city_str}': {e}")
                
    except Exception as e:
        logger.exception(f"[DaData]: Критическая авария при инициализации сессии DaData: {e}")

    logger.info(f"[DaData]: Завершено. Успешно распознаны fias_id городов: {len(city_to_fias)} из {len(unique_cities)}.")
    return city_to_fias