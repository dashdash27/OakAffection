import os

class DeliveryConfig:
    YANDEX_DELIVERY = {
        "URL_GEO_ID": "https://b2b.taxi.yandex.net/api/b2b/platform/location/detect",
        "URL_POINTS_LIST": "https://b2b.taxi.yandex.net/api/b2b/platform/pickup-points/list",
        "URL_PRICING_CALCULATOR": "https://b2b.taxi.yandex.net/api/b2b/platform/pricing-calculator",
        "API_TOKEN": os.getenv("YANDEX_DELIVERY_TOKEN"),
        "SOURCE_PVZ_ID": os.getenv("YANDEX_SOURCE_ID"),

        "MARGIN_MULTIPLIER": 1.1,
        "SAFE_BOX_WEIGHT": 15000,

        "POINTS_PROFILES": {
            # Обычные ПВЗ Яндекса
            "point": {
                "order": {"weight": 200000, "sum": 500, "side": 300},
                "box":   {"weight": 30000,  "sum": 300, "side": 150}
            },
            # ПВЗ Пятерочки (5Post)
            "five_post_postamat": {
                "order": {"weight": 11000,  "sum": 136, "side": 64},
                "box":   {"weight": 11000,  "sum": 136, "side": 64}
            },
            # Постаматы Яндекса
            "postamat": {
                "order": {"weight": 20000,  "sum": 118, "side": 40},
                "box":   {"weight": 20000,  "sum": 118, "side": 40}
            }
        },

        "REMOTE_REGION_LIMITS": {
            "weight": 15000,  # 15 кг
            "sum": 180,       # 180 см
            "side": 60        # 60 см
        },

        "REMOTE_REGIONS_DADATA_FIAS_IDS": {
            "844a80d6-5e31-4017-b422-4d9c01e9942c", # Амурская область
            "6466c988-7ce3-45e5-8b97-90ae16cb1249", # Иркутская область
            "43909681-d6e1-432d-b61f-ddac393cb5da", # Приморский край
            "7d468b39-1afa-41ec-8c4f-97a8603cb3d4", # Хабаровский край
            "294277aa-e25d-428c-95ad-46719c4ddb44", # Архангельская область
            "1c727518-c96a-4f34-9ae6-fd510da3be03", # Мурманская область
            "248d8071-06e1-425e-a1cf-d1ff4c4a14a8", # Республика Карелия
            "c20180d9-ad9c-46d1-9eff-d60bc424592a", # Республика Коми
            "8d3f1d35-f0f4-41b5-b5b7-e7cadf3e7bd7", # Республика Хакасия
        }
    }

    RUSSIAN_POST = {
        "API_TOKEN": os.getenv("RUSSIAN_POST_API_TOKEN"),
        "API_KEY": os.getenv("RUSSIAN_POST_API_KEY"),
        "INDEX_FROM": os.getenv("RUSSIAN_POST_INDEX_FROM"),
        "URL_POINTS_LIST": "https://otpravka-api.pochta.ru//postoffice/1.0/nearby?",
        "URL_PRICING_CALCULATOR": "https://otpravka-api.pochta.ru/1.0/tariff",

        "MARGIN_MULTIPLIER": 1.1,

        "GLOBAL_WEIGHT_LIMIT": 200000,
        "ORDER_WEIGHT_LIMIT": 20000,
        "MAX_SIDE_SUM": 300,

        "GEO_SEARCH_SETTINGS": {
            "RADIUS_BY_FIAS_LEVEL": {
                1: 50,
                4: 10,
            },
            "DEFAULT_RADIUS": 30
        }
    }