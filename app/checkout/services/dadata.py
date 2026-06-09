import requests
import random
from flask import current_app

dadata_session = requests.Session()

def get_dadata_session():
    if 'Authorization' not in dadata_session.headers:
        api_key = current_app.config.get('DADATA', {}).get('API_KEY')
        dadata_session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {api_key}"
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
        "postal_code": data.get('postal_code'),
        "settlement": data.get('city') or data.get('settlement') or ""
    }

def get_city_suggestions(query): 
    if False:
        mock_data = [
            {"value": "г Москва", "region_fias_id": "29251dcf-00a1-4e34-98d4-5c47484a36d4"},
            {"value": "г Краснодар", "region_fias_id": "d00e1013-16bd-4c09-b3d5-3cb09fc54bd8"},
            {"value": "г Мурманск", "region_fias_id": "1c727518-c96a-4f34-9ae6-fd510da3be03"}
        ]
        mock_data = [format_suggestion(s) for s in mock_data]
        random.shuffle(mock_data)
        return mock_data
    
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
    except (requests.exceptions.RequestException, Exception) as e:
        print(f"Ошибка при запросе к Dadata: {e}")
        return None 