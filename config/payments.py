import os

class PaymentsConfig:
    OZON_PAY = {
        "ACCESS_KEY": os.getenv("OZON_PAY_ACCESS_KEY"),
        "SECRET_KEY": os.getenv("OZON_PAY_SECRET_KEY"),
        "URL_CREATE_ORDER": "https://payapi.ozon.ru/v1/createOrder",
    }