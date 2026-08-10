import os

class PaymentsConfig:
    _base_url = os.getenv('BASE_URL')

    OZON_PAY = {
        "ACCESS_KEY": os.getenv("OZON_PAY_ACCESS_KEY"),
        "SECRET_KEY": os.getenv("OZON_PAY_SECRET_KEY"),
        "NOTIFICATION_KEY": os.getenv("OZON_PAY_NOTIFICATION_KEY"),
        "URL_CREATE_ORDER": "https://payapi.ozon.ru/v1/createOrder",
        "NOTIFICATION_URL": f"{_base_url}/payments/api/ozon-pay-webhook",
        "SUCCESS_URL": f"{_base_url}/checkout/success",
        "FAILURE_URL": f"{_base_url}/checkout/failure",
        "ORDER_PREFIX": os.getenv("OZON_PAY_ORDER_PREFIX")
    }