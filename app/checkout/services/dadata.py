from app.logger import logger

import requests
from flask import current_app

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