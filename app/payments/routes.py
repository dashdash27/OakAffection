from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
import json
import os, hashlib

from app import csrf
from app.extensions import db
from app.models import Order, PaymentStatus, OrderStatus
from app.payments.utils import generate_ozon_pay_notification_sign

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/api/ozon-pay-webhook', methods=['POST'], strict_slashes=False)
@csrf.exempt
def ozon_pay_webhook():
    print("==== Получен Webhook от Ozon Pay ====)")
    data = request.get_json(silent=True)

    if not data:
        print("Получен пустой вебхук или данные не в формате JSON")
        return "Invalid JSON", 400
    
    pretty_json = json.dumps(data, indent=4, ensure_ascii=False)
    print(f"{pretty_json}")

    # 1. Отсев самостоятельных попыток оплаты. Если нет orderID - самостоятельная оплата
    if "orderID" not in data or not data["orderID"]:
        print("Это самостоятельная оплата")
        return "Ignored independent payment", 200
    
    # 2. Проверка подписи
    computed_signature = generate_ozon_pay_notification_sign(data)
    request_sign = data.get("requestSign")

    if computed_signature != request_sign:
        print(f"-> [ОШИБКА]: Подпись не совпала! Ожидалось: {computed_signature}, пришло: {request_sign}")
        return "Invalid signature", 400
    
    print(f"Подпись совпала: {computed_signature}")

    # 3. Ищем заказ по my_order_id в БД и его платеж
    my_order_id_raw = data.get("extOrderID")
    try:
        my_order_id = int(my_order_id_raw.split('-', 1)[1])
    except (ValueError, IndexError, AttributeError):
        print(f"-> [ОШИБКА]: Некорректный формат extOrderID: {my_order_id_raw}")
        return "Missing extOrderID", 400

    order = Order.query.filter(Order.id == my_order_id).first()

    if not order:
        print(f"Заказ #{my_order_id} отсутствует в нашей БД!")
        return "Order not found", 400
    
    # Получаем уже существующую платежку, привязанную к заказу
    payment = order.payment  
    if not payment:
        print(f"-> [ОШИБКА]: К заказу #{my_order_id} не привязана платежка в БД!")
        return "Payment record not found for this order", 400

    # 4. Обработка статуса
    status_ozon = data.get("status")
    print(f"Статус заказа в Ozon Pay: {status_ozon}")

    tx_id_raw = data.get("transactionID")
    tx_uid_raw = data.get("transactionUid") or data.get("transactionUID")

    if status_ozon == "Completed":
        print(f"Переводим заказ #{my_order_id} и платеж в статус 'paid'/'completed'...")
        
        try:
            order.status = OrderStatus.PAID
            payment.status = PaymentStatus.COMPLETED
            
            if tx_uid_raw or tx_id_raw:
                payment.external_id = str(tx_uid_raw) if tx_uid_raw else str(tx_id_raw)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при сохранении успешного платежа в БД: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    elif status_ozon == "Rejected":
        print(f"-> Переводим платежку заказа #{my_order_id} в статус 'rejected'...")

        try:
            if  not (payment.status == PaymentStatus.COMPLETED and order.status == OrderStatus.PAID):
                order.status = OrderStatus.PENDING
                payment.status = PaymentStatus.REJECTED
                
                if tx_uid_raw or tx_id_raw:
                    payment.external_id = str(tx_uid_raw) if tx_uid_raw else str(tx_id_raw)
                
                db.session.commit()
            else:
                print("-> Платежка уже завершена, ничего не делаем")
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при сохранении отклоненного платежа в БД: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    else:
        print(f"-> Получен необрабатываемый статус: {status_ozon}")
        return {"status": "unhandled_status"}, 200
    
    print("==== Вебхук успешно обработан и записан в БД ====")
    return {"status": "success"}, 200