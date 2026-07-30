from app.models import Order 
from app.payments.utils import generate_ozon_pay_sign, generate_ozon_expires_at
from app.checkout.core.utils import generate_order_hash

import requests
import json
from datetime import timedelta

ozon_pay_session = requests.Session()

def get_ozon_pay_session():
    ozon_pay_session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    return ozon_pay_session


def request_ozon_pay_link(order: Order, ozon_pay_cfg: dict) -> str | None:
    url = ozon_pay_cfg.get("URL_CREATE_ORDER")
    access_key = ozon_pay_cfg.get("ACCESS_KEY")

    notification_url = ozon_pay_cfg.get("NOTIFICATION_URL")
    base_success_url = ozon_pay_cfg.get("SUCCESS_URL")
    base_failure_url = ozon_pay_cfg.get("FAILURE_URL")
    order_prefix = ozon_pay_cfg.get("ORDER_PREFIX")

    token = generate_order_hash(order.id)

    success_url = f"{base_success_url}?order_id={order.id}&token={token}"
    failure_url = f"{base_failure_url}?order_id={order.id}&token={token}"

    if not url or not access_key:
        print("[OZON PAY ERROR] Не настроены URL_CREATE_ORDER или ACCESS_KEY в конфигурации.")
        return None

    # Add Order Items
    ozon_items = []
    for item in order.items:
        ozon_items.append({
            "extId": f"{item.product_id}",
            "name": f"{item.product_name}",
            "price": {
                "currencyCode": "643",
                "value": str(item.price_with_discount)
            },
            "quantity": item.quantity,
            "type": "TYPE_PRODUCT",
            "vat": "VAT_5"
        })

    # Add Delivery
    if order.delivery_price > 0:
        ozon_items.append({
            "name": f"Доставка ({order.delivery_service.value})",
            "price": {
                "currencyCode": "643",
                "value": str(order.delivery_price)
            },
            "quantity": 1,
            "type": "TYPE_SERVICE",
            "vat": "VAT_5"
        })

    # Final Payload
    payload = {
        "accessKey": access_key,
        "amount": {
            "currencyCode": "643",
            "value": str(order.total_amount)
        },
        "enableFiscalization": True,
        "expiresAt": generate_ozon_expires_at(30),
        "extId": f"{order_prefix}{order.id}",
        "failUrl": failure_url,
        "fiscalizationPhone": order.customer_phone,
        "fiscalizationType": "FISCAL_TYPE_SINGLE",
        "items": ozon_items,
        "mode": "MODE_FULL",
        "notificationUrl": notification_url,
        "paymentAlgorithm": "PAY_ALGO_SMS",
        "receiptEmail": order.customer_email,
        "successUrl": success_url
    }
    # generate sign
    payload["requestSign"] = generate_ozon_pay_sign(payload)
    print(json.dumps(payload, indent=4, ensure_ascii=False))

    try:
        session = get_ozon_pay_session()
        response = session.post(url, json=payload, timeout=5)
        response.raise_for_status() 

        response_data = response.json() or {}
        order_data = response_data.get('order') or {}

        ext_order_id = order_data.get('id')
        pay_link = order_data.get('payLink')
        
        return pay_link, ext_order_id

    except requests.exceptions.RequestException as req_err:
        print(f"[OZON PAY HTTP ERROR] Сбой API для заказа {order.id}: {req_err}")
        return None, None
    except Exception as e:
        print(f"[OZON PAY ERROR] Непредвиденная ошибка парсинга ответа: {e}")
        return None, None
