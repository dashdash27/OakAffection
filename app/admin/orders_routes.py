from app.admin.routes import admin_bp 
from app.models import Order, OrderStatus, PaymentStatus
from app.extensions import db


from flask import render_template, request, jsonify, request


@admin_bp.route('/orders', methods=['GET'])
def orders():
    status_filter = request.args.get('status')

    query = Order.query.order_by(Order.created_at.desc())

    if status_filter == 'active':
        query = query.filter(Order.status != OrderStatus.CANCELLED)
        
    elif status_filter:
        try:
            enum_status = OrderStatus(status_filter)
            query = query.filter(Order.status == enum_status)
        except ValueError:
            status_filter = None

    orders = query.all()

    return render_template('admin/orders/home.html', orders=orders, current_status=status_filter)

@admin_bp.route('/orders/<int:order_id>', methods=['GET', 'POST'])
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    payment = order.payment

    # Определяем какие действия доступны в зависимости от статуса заказа
    show_buttons = {
        "ship": False,       # Отправить
        "deliver": False,    # Доставлен
        "rollback_sent": False, # Ошибся (вернуть в Отправлен)
        "rollback_paid": False, # Ошибся (вернуть в Оплачен)
        "refund_mark": False,   # Отметить возврат
        "refund_cancel": False  # Отменить возврат (в paid)
    }

    # 1. Заказ оплачен, но еще не отправлен -> отправить, возврат
    if order.status == OrderStatus.PAID and payment.status == PaymentStatus.COMPLETED:
        show_buttons["ship"] = True
        show_buttons["refund_mark"] = True
    
    # 2. Заказ в пути (Отправлен) -> доставлен, возврат, вернуть в paid
    elif order.status == OrderStatus.SENT and payment.status == PaymentStatus.COMPLETED:
        show_buttons["deliver"] = True
        show_buttons["rollback_paid"] = True

    # 3. Финал: Доставлен -> ошибся в sent, возврат
    elif order.status == OrderStatus.DELIVERED and payment.status == PaymentStatus.COMPLETED:
        show_buttons["rollback_sent"] = True
        show_buttons["refund_mark"] = True

    # 4. Финал: Оформлен ручной возврат -> отменить возврат
    elif order.status == OrderStatus.RETURNED and payment.status == PaymentStatus.COMPLETED:
        show_buttons["refund_cancel"] = True

    return render_template('admin/orders/detail.html', order=order, buttons=show_buttons)

@admin_bp.route('/orders/<int:order_id>/action', methods=['POST'])
def change_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    payment = order.payment

    req_data = request.get_json(silent=True)
    if not req_data:
        return jsonify({"success": False, "error": "Тело запроса должно быть в формате JSON"}), 400
    
    action = req_data.get('action')
    if not action:
        return jsonify({"success": False, "error": "Не передан обязательный параметр 'action'"}), 400
    
    if not payment or payment.status != PaymentStatus.COMPLETED:
        return jsonify({"success": False, "error": "Действие невозможно: заказ не оплачен"}), 400
    
    try:
        # Действие: Отправить заказ (PAID -> SENT)
        if action == 'ship' and order.status == OrderStatus.PAID:
            order.status = OrderStatus.SENT

        # Действие: Отметить как доставлен (SENT -> DELIVERED)
        elif action == 'deliver' and order.status == OrderStatus.SENT:
            order.status = OrderStatus.DELIVERED

        # Страховка: Админ ошибся (DELIVERED -> SENT)
        elif action == 'rollback_sent' and order.status == OrderStatus.DELIVERED:
            order.status = OrderStatus.SENT

        # Страховка: Админ ошибся (SENT -> PAID)
        elif action == "rollback_paid" and order.status == OrderStatus.SENT:
            order.status = OrderStatus.PAID

        # Действие: Отметить ручной возврат (Строго PAID или DELIVERED -> RETURNED)
        elif action == 'refund_mark' and order.status in [OrderStatus.PAID, OrderStatus.DELIVERED]:
            order.status = OrderStatus.RETURNED

        # Действие: Отменить возврат (RETURNED -> PAID)
        elif action == 'refund_cancel' and order.status == OrderStatus.RETURNED:
            order.status = OrderStatus.PAID

        else:
            return jsonify({
                "success": False, 
                "error": f"Действие '{action}' недопустимо для текущего статуса заказа ({order.status.value})"
            }), 400
        
        db.session.commit()
        print(f"-> [Админка Успех]: Статус заказа #{order_id} изменен на {order.status.value}")
        return jsonify({"success": True}), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"-> [Админка Ошибка]: Ошибка транзакции при действии {action} для заказа #{order_id}: {e}")
        return jsonify({"success": False, "error": "Внутренняя ошибка сервера при записи в БД"}), 500
    

@admin_bp.route('/orders/<int:order_id>/track', methods=['POST'])
def save_order_track(order_id):
    order = Order.query.get_or_404(order_id)
    
    req_data = request.get_json(silent=True)
    delivery_track = req_data.get('delivery_track', '').strip()

    if not delivery_track:
        return jsonify({"success": False, "error": "Пустой трек-номер"}), 400

    try:
        # 1. Сохраняем трек в модель заказа
        order.delivery_track = delivery_track
        
        # 2. TODO: Отправляем письмо на EMAIL:
        # send_track_email(email=order.user.email, track=track_number)
        print(f"-> [Email]: Письмо с треком {delivery_track} отправлено для заказа #{order_id}")

        db.session.commit()
        return jsonify({"success": True}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500