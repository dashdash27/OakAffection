import os
import hashlib

def generate_ozon_pay_sign(payload: dict) -> str:
    secret_key = os.getenv("OZON_PAY_SECRET_KEY")

    fingerprint = (
        f"{payload['accessKey']}"
        f"{payload['extId']}"
        f"{payload['fiscalizationType']}"
        f"{payload['paymentAlgorithm']}"
        f"{payload['amount']['currencyCode']}{payload['amount']['value']}"
        f"{secret_key}"
    )

    request_sign = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()

    return request_sign

def generate_ozon_pay_notification_sign(payload: dict) -> str:
    access_key = os.getenv("OZON_PAY_ACCESS_KEY")
    notification_key = os.getenv("OZON_PAY_NOTIFICATION_KEY")

    ozon_order_id = payload.get("orderID")
    my_order_id_raw = payload.get("extOrderID") or ""

    tx_id_raw = payload.get("transactionID")
    tx_uid_raw = payload.get("transactionUid") or payload.get("transactionUID")
    transaction_identifier_for_sign = tx_id_raw if tx_id_raw is not None else tx_uid_raw

    amount = payload.get("amount")
    currency_code = payload.get("currencyCode")

    digest = (
        f"{access_key}|"
        f"{ozon_order_id}|"
        f"{transaction_identifier_for_sign}|"
        f"{my_order_id_raw}|"
        f"{amount}|"
        f"{currency_code}|"
        f"{notification_key}"
    )

    computed_signature = hashlib.sha256(digest.encode('utf-8')).hexdigest()

    return computed_signature