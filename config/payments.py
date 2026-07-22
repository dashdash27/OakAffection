import os

class PaymentsConfig:
    OZON_PAY = {
        "ACCESS_KEY": os.getenv("OZON_PAY_ACCESS_KEY"),
        "SECRET_KEY": os.getenv("OZON_PAY_SECRET_KEY"),
        "NOTIFICATION_KEY": os.getenv("OZON_PAY_NOTIFICATION_KEY"),
        "URL_CREATE_ORDER": "https://payapi.ozon.ru/v1/createOrder",
        "NOTIFICATION_URL": "http://glwjr-31-181-18-84.free.pinggy.net/payments/api/ozon-pay-webhook",
        "ORDER_PREFIX": "LOCAL1-"
    }