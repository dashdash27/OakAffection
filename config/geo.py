import os

class GeoConfig:
    DADATA = {
        "URL_ADDRESS_SUGGESTIONS": "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address",
        "API_KEY": os.getenv("DADATA_API_KEY")
    }