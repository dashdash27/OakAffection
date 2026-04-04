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
        "fias_id": data.get('fias_id')
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
    except (requests.exceptions.RequestException, Exception) as e:
        print(f"Ошибка при запросе к Dadata: {e}")
        return None 