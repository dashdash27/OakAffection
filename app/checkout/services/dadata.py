import requests
import random
from config import Config

DADATA_API_KEY = Config.DADATA_API_KEY

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Token {DADATA_API_KEY}"
})

def format_suggestion(s):
    data = s.get('data', {})
    return {
        "value": s.get('value'),
        "unrestricted_value": s.get('unrestricted_value'),
        "fias_id": data.get('fias_id')
    }

def get_city_suggestions(query): 
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"

    data = {
        "query": query, 
        "from_bound": {"value": "city"}, 
        "to_bound": {"value": "settlement"}
    }
    
    try:
        response = session.post(url, json=data, timeout=5)
        response.raise_for_status() 

        suggestions = response.json().get('suggestions', [])

        return [format_suggestion(s) for s in suggestions]
    except (requests.exceptions.RequestException, Exception) as e:
        print(f"Ошибка при запросе к Dadata: {e}")
        return None 