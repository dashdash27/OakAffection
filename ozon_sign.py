import hashlib
import os

access_key = os.getenv("OZON_PAY_ACCESS_KEY")
secret_key = os.getenv("OZON_PAY_SECRET_KEY")

ext_id = 'my1'
expires_at = ''
fiscalization_type = 'FISCAL_TYPE_SINGLE'
payment_algorithm = 'PAY_ALGO_SMS'
amount = {'currencyCode': '643', 'value': '100000'}

fingerprint = (
    f"{access_key}"
    f"{expires_at}"
    f"{ext_id}"
    f"{fiscalization_type}"
    f"{payment_algorithm}"
    f"{amount['currencyCode']}{amount['value']}"
    f"{secret_key}"
)

print(fingerprint)

request_sign = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()

print(request_sign)