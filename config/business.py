import os

class BusinessConfig:
    PARCEL_FALLBACKS = {
        "PRODUCT_WEIGHT_G": 500,
        "WRAPPER_LENGTH_CM": 10,
        "WRAPPER_HEIGHT_CM": 10,
        "WRAPPER_DEPTH_CM": 10,
    }

    DELIVERY_SAFETY_FACTORS = {
        "TOTAL_WEIGHT": 1.08,
        "MAX_ITEM_WEIGHT": 1.05,
        "MAX_ITEM_SIDE": 1.05,
        "CUBIC_SUM": 1.2
    }

    CATEGORIES_DICT = {
        'oils': 'Масла для обработки дерева',
        'indoor_oils': 'Масла для внутренних работ',
        'outdoor_oils': 'Масла для наружных работ',
        'other_oils': 'Другие масла',
        'kitchen_oils': 'Масла для кухонной утвари',
        'furniture_oils': 'Масла для мебели',
        'toy_oils': 'Масла для игрушек',
        'bath_oils': 'Масла для бань и саун',
        'terrace_oils': 'Масла для террас',
        'garden_furniture_oils': 'Масла для садовой мебели',
        'facade_oils': 'Масла для фасадов',
        'tinted_oils': 'Колерованные масла',
        'liquids': 'Грунтовочные масла и растворители'
    }