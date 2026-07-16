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