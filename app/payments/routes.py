from flask import Blueprint, request, jsonify

from app import csrf
from app.extensions import db, limiter
from app.logger import logger
from app.models import Order, PaymentStatus, OrderStatus
from app.payments.utils import generate_ozon_pay_notification_sign
from app.services.email import send_order_confirmation_email

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/api/ozon-pay-webhook', methods=['POST'], strict_slashes=False)
@csrf.exempt
@limiter.exempt
def ozon_pay_webhook():
    try:
        raw_bytes = request.get_data()
        logger.debug(f"=== Получен сырой Webhook от Ozon Pay ===. Тело: {raw_bytes.decode('utf-8')}")
    except Exception:
        logger.exception("Не удалось прочитать сырые байты входящего вебхука")

    # Парсим json
    data = request.get_json(silent=True)
    if not data:
        logger.warning("Вебхук отклонен: пустые данные или невалидный формат JSON")
        return "Invalid JSON", 400
    
    # 1. Отсев самостоятельных попыток оплаты. Если нет orderID - самостоятельная оплата
    if "orderID" not in data or not data["orderID"]:
        logger.info(f"Игнорируем самостоятельную оплату внутри Ozon. ExtOrderID: {data.get('extOrderID', 'Нет данных')}")
        return "Ignored independent payment", 200
    
    # 2. Проверка подписи
    computed_signature = generate_ozon_pay_notification_sign(data)
    request_sign = data.get("requestSign")

    if computed_signature != request_sign:
        logger.error(f"Контроль подписи провален! Ожидалось: {computed_signature}, пришло: {request_sign}. JSON: {data}")
        return "Invalid signature", 400
    
    logger.debug(f"Криптографическая подпись Ozon Pay успешно подтверждена: {computed_signature}")

    # 3. Ищем заказ по my_order_id в БД и его платеж
    my_order_id_raw = data.get("extOrderID")
    try:
        my_order_id = int(my_order_id_raw.split('-', 1)[1])
    except (ValueError, IndexError, AttributeError):
        logger.error(f"Не удалось распарсить локальный ID заказа из extOrderID. Получено: '{my_order_id_raw}'")
        return "Missing extOrderID", 400

    try:
        order = Order.query.filter(Order.id == my_order_id).first()
    except Exception:
        logger.exception(f"Системный сбой БД при поиске заказа №{my_order_id} во время вебхука")
        return "Database error", 500

    if not order:
        logger.error(f"Вебхук отклонен: Заказ №{my_order_id} физически отсутствует в нашей базе данных!")
        return "Order not found", 400
    
    # Получаем уже существующую платежку, привязанную к заказу
    payment = order.payment  
    if not payment:
        logger.error(f"Вебхук отклонен: К существующему заказу №{my_order_id} в БД не привязана таблица платежа!")
        return "Payment record not found for this order", 400

    # 4. Обработка статуса
    status_ozon = data.get("status")
    tx_id_raw = data.get("transactionID")
    tx_uid_raw = data.get("transactionUid") or data.get("transactionUID")

    logger.debug(f"Начало обработки статуса Ozon Pay. Заказ №{order.id}, Статус шлюза: {status_ozon}, TxID: {tx_id_raw}")

    if status_ozon == "Completed":
        logger.info(f"Получен вебхук успеха от Ozon Pay. Переводим заказ №{order.id} в статус PAID, а платеж в статус COMPLETED.")
        
        try:
            order.status = OrderStatus.PAID
            payment.status = PaymentStatus.COMPLETED
            
            if tx_uid_raw or tx_id_raw:
                payment.external_id = str(tx_uid_raw) if tx_uid_raw else str(tx_id_raw)

            db.session.commit()

            logger.info(f"Заказ №{order.id} успешно подтвержден оплатой в БД.")

            # Отправляем письмо-подтверждение клиенту
            send_order_confirmation_email(order.customer_email, order.id)
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Критическая ошибка фиксации успешной оплаты в БД для заказа №{order.id}")
            return jsonify({"success": False, "error": "DATABASE_ERROR"}), 500
    
    elif status_ozon == "Rejected":
        try:
            if  not (payment.status == PaymentStatus.COMPLETED and order.status == OrderStatus.PAID):
                logger.info(f"Получен вебхук отказа от Ozon Pay. Переводим платеж заказа №{order.id} в статус REJECTED.")

                order.status = OrderStatus.PENDING
                payment.status = PaymentStatus.REJECTED
                
                if tx_uid_raw or tx_id_raw:
                    payment.external_id = str(tx_uid_raw) if tx_uid_raw else str(tx_id_raw)
                
                db.session.commit()
            else:
                logger.warning(f"Ozon прислал статус Rejected на уже ОПЛАЧЕННЫЙ заказ №{order.id}. Действие проигнорировано.")
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Критическая ошибка при сохранении отклоненного платежа в БД для заказа №{order.id}")
            return jsonify({"success": False, "error": "DATABASE_ERROR"}), 500

    else:
        logger.warning(f"Получен необрабатываемый статус от Ozon Pay: '{status_ozon}' для заказа №{order.id}")
        return jsonify({"status": "unhandled_status"}), 200
    
    logger.info(f"==== Вебхук Ozon Pay для заказа №{order.id} успешно обработан и закрыт ====")
    return jsonify({"status": "success"}), 200