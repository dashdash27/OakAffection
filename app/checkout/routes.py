from app.logger import logger
from app.models import Product, PaymentStatus, Order, OrderStatus
from app.extensions import limiter, db
from .utils import process_cart, calculate_order_dimensions, calculate_cart_base_total
from .schemas import OrderCreateSchema 
from .core.order_creator import create_new_order_transaction
from app.payments.services.ozon_pay import request_ozon_pay_link
from app.checkout.core.utils import verify_and_get_delivery_price
from app.checkout.core.utils import validate_order_totals, allocate_items_discount, verify_order_hash, generate_order_hash

from .services.dadata import get_city_suggestions
from .services.yandex import get_yandex_delivery_info
from .services.russian_post import get_russian_post_delivery_info

import asyncio
import httpx
from flask import Blueprint, render_template, request, jsonify, current_app
from pydantic import ValidationError


checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

@checkout_bp.route('/cart')
def cart():
    return render_template('checkout/cart.html')

@checkout_bp.route('/details')
def checkout():
    return render_template('checkout/checkout.html')

@checkout_bp.route('/api/cart/sync', methods=['POST'])
@limiter.limit("10 per second; 150 per minute")
def sync_cart():
    data = request.get_json()
    if not data or 'product_ids' not in data:
        logger.warning(f"Некорректный запрос синхронизации корзины. Тело запроса: {data}")
        return jsonify({"success": False, "error": "BAD_REQUEST"}), 400
    
    raw_ids = data.get('product_ids', [])
    logger.debug(f"Фронтенд передал {len(raw_ids)} ID товаров для проверки")

    clean_ids = []
    for pid in raw_ids:
        try:
            clean_ids.append(int(pid))
        except (ValueError, TypeError):
            continue
    
    products = Product.query.filter(Product.id.in_(clean_ids)).all()

    result = []
    for p in products:
        if not p.price:
            continue
        
        photo_path = p.photos[0].photo_url if p.photos else "img/icons/nophoto.png"

        result.append({
            "id": p.id,
            "name": p.name,
            "price": int(p.price),
            "photo_path": f"/static/{photo_path}",
            "slug": p.slug
        })

    discount_thresholds = current_app.config.get("DISCOUNT_THRESHOLDS", [])
    discount_rules = []
    for step in discount_thresholds:
        discount_rules.append({
            "threshold": step.get("min_amount_rub"),
            "value": step.get("discount_percent") / 100,
            "label": f"{step.get('discount_percent')}%"
        })

    logger.debug(f"Успешная синхронизация корзины: найдено в БД {len(result)} товаров")
    
    return jsonify({
        "products": result,
        "discount_rules": discount_rules
    }), 200

@checkout_bp.route('/api/suggestions/cities', methods=['POST'])
@limiter.limit("30 per minute")
def suggest_cities():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    
    if len(query) < 3:
        return jsonify([]), 200
    
    city_suggestions = get_city_suggestions(query)

    if city_suggestions is None:
        logger.warning(f"Не удалось получить подсказки городов для запроса: {query}")
        return jsonify({"success": False, "error": "EXTERNAL_SERVICE_ERROR"}), 502

    logger.debug(f"Успешно получено {len(city_suggestions)} подсказок для города: {query}")
    return jsonify(city_suggestions), 200

@checkout_bp.route('/api/delivery/options', methods=['POST'])
@limiter.limit("20 per minute")
async def get_delivery_options():
    req_data = request.get_json()

    if not req_data or 'city_data' not in req_data or 'cart' not in req_data:
        logger.warning(f"Некорректный запрос вариантов доставки. Тело запроса: {req_data}")
        return jsonify({"success": False, "error": "BAD_REQUEST"}), 400
    
    city_data = req_data.get('city_data')
    cart = req_data.get('cart')
    
    city_name = city_data.get('value', 'Неизвестный город')
    logger.debug(f"Начало расчета вариантов доставки для города: {city_name}")
    
    order_items = process_cart(cart)
    order_dimensions = calculate_order_dimensions(order_items)
    order_price = calculate_cart_base_total(order_items)

    yandex_config = current_app.config.get("YANDEX_DELIVERY", {})
    russian_post_config = current_app.config.get("RUSSIAN_POST", {})

    # Create 1 client for all requests of this user
    async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
        tasks = [
            get_yandex_delivery_info(city_data, order_dimensions, client, yandex_config),
            get_russian_post_delivery_info(city_data, order_dimensions, order_price, client, russian_post_config)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    yandex_result = results[0]
    russian_post_result = results[1]
    
    if isinstance(yandex_result, Exception):
        logger.exception(f"Глобальный сбой asyncio для Яндекса (city: {city_name}): {yandex_result}")
        yandex_delivery_info = {
            "status": "tech_error",
            "error_code": "YANDEX_API_DOWN",
            "message": "Служба доставки Яндекса временно недоступна."
        }
    else:
        yandex_delivery_info = yandex_result

    if isinstance(russian_post_result, Exception):
        logger.exception(f"Глобальный сбой asyncio для Почты России (city: {city_name}): {russian_post_result}")
        russian_post_delivery_info = {
            "status": "tech_error",
            "error_code": "RUSSIAN_POST_API_DOWN",
            "message": "Служба доставки Почты России временно недоступна."
        }
    else:
        russian_post_delivery_info = russian_post_result

    logger.debug(f"Закончен расчет вариантов доставки для города: {city_name}")
    return jsonify({
        "status": "success",
        "cart_metrics": {
            "total_weight": order_dimensions["total_weight"],
            "cubic_sum_of_sides": order_dimensions["cubic_sum_of_sides"]
        },
        "deliveries": {
            "yandex": yandex_delivery_info,
            "post": russian_post_delivery_info
        }
    }), 200

@checkout_bp.route('/api/orders', methods=['POST'])
def create_order():
    raw_data = request.get_json()
    if not raw_data:
        return jsonify({"success": False, "error": "Недостаточно данных для создания заказа"}), 422
    
    logger.debug(f"Получен запрос на создание заказа: {raw_data}")

    # 1. Validation
    try:
        validated_order = OrderCreateSchema(**raw_data)
    except ValidationError as e:
        logger.warning(f"Ошибка валидации Pydantic. Ошибки: {e.errors()}. JSON: {raw_data}")
        return jsonify({"success": False, "error": "VALIDATION_ERROR"}), 422
    
    try:
        # 2. Checking JWT Token
        logger.debug("Проверка JWT токена доставки")
        trusted_delivery_price = verify_and_get_delivery_price(validated_order.delivery.delivery_token)
        
        # 3. Calculate total_amount and compare
        totals_match, order_items, discount_amount, items_discounted_total = validate_order_totals(
            cart=validated_order.cart,
            trusted_delivery_price=trusted_delivery_price,
            client_total_amount=validated_order.client_total_amount
        )
        if not totals_match:
            logger.warning(f"Рассинхронизация сумм корзины у пользователя. Client Total Amount: {validated_order.client_total_amount}")
            return jsonify({"success": False, "error": "PRICE_MISMATCH"}), 422
        
        # 4. Распределяем скидку на товары
        items_base_total = items_discounted_total + discount_amount
        allocated_items = allocate_items_discount(order_items, items_base_total, items_discounted_total)

        # 5. Create order
        enriched_delivery = validated_order.delivery.model_copy(update={
            "price": trusted_delivery_price
        })
        server_total_amount = items_discounted_total + trusted_delivery_price
        final_order_to_save = validated_order.model_copy(update={
            "delivery": enriched_delivery,
            "discount_amount": discount_amount,
            "total_amount": server_total_amount,
            "order_items": allocated_items
        })
        
        order = create_new_order_transaction(final_order_to_save)
        logger.info(f"Заказ успешно создан локально в БД. ID Заказа: {order.id}, Сумма: {server_total_amount} руб.")

        # 6. Create order in ozon pay
        ozon_pay_cfg = current_app.config.get("OZON_PAY", {})

        pay_link, ext_order_id = request_ozon_pay_link(order, ozon_pay_cfg)

        if pay_link is None or ext_order_id is None:
            try:
                order.payment.status = PaymentStatus.CREATION_FAILED
                db.session.commit()
            except Exception as e:
                logger.exception(f"Не удалось перевести платеж заказа №{order.id} в статус CREATION_FAILED при ошибке шлюза")
                db.session.rollback()
                return jsonify({"success": False, "error": "DATABASE_ERROR"}), 500
            
            logger.warning(f"Заказ №{order.id} сохранен со статусом CREATION_FAILED (Ozon Pay не вернул ссылку или внешний id).")
            return jsonify({"success": False, "error": "PAYMENT_GATEWAY_ERROR"}), 502

        try:
            order.ext_id = ext_order_id  
            db.session.commit()
        except Exception as e:
            logger.exception(f"Ошибка сохранения ext_id={ext_order_id} для заказа №{order.id}. Откат транзакции.")
            db.session.rollback()

            try:
                order.payment.status = PaymentStatus.CREATION_FAILED
                db.session.commit()
            except Exception:
                logger.warning(f"Ошибка перевода статуса оплаты в CREATION_FAILED для заказа №{order.id}. Откат транзакции.")
                db.session.rollback()

            return jsonify({"success": False, "error": "DATABASE_ERROR"}), 500

        logger.info(f"Платежная ссылка успешно привязана к заказу №{order.id}. Клиент перенаправляется на оплату.")
        return jsonify({
            "success": True, 
            "order_id": order.id, 
            "pay_link": pay_link,
            "token": generate_order_hash(order.id)
        }), 200

    except ValueError as val_err:
        logger.warning(f"Ошибка при проверки токена доставки")
        return jsonify({"success": False, "error": "DELIVERY_ERROR"}), 422
    
    except Exception as e:
        logger.exception("Критическая непредвиденная ошибка на этапе оформления заказа")
        return jsonify({"success": False, "error": "INTERNAL_SERVER_ERROR"}), 500

    
@checkout_bp.route('/success', methods=['GET'])
def success_page():
    """Success payment page. Логика проверок будет на JS."""
    return render_template('/checkout/success.html')

@checkout_bp.route('/failure', methods=['GET'])
def failure_page():
    """Failure payment page. Логика проверок будет на JS."""
    return render_template('/checkout/failure.html')


@checkout_bp.route('/api/orders/<int:order_id>/status', methods=['GET'])
def get_single_order_status(order_id):
    """Проверка статуса одного заказа"""
    client_token = request.args.get('token')

    if not verify_order_hash(order_id, client_token):
        logger.warning(f"Отказ в доступе (403): Невалидный токен '{client_token}' для заказа №{order_id}")
        return jsonify({"success": False, "error": "FORBIDDEN"}), 403

    try:
        order = Order.query.get(order_id)
    except Exception:
        logger.exception(f"Системный сбой БД при опросе статуса заказа №{order_id}")
        return jsonify({"success": False, "error": "DATABASE_ERROR"}), 500
    
    if not order:
        logger.warning(f"Заказ №{order_id} не найден в БД при опросе статуса, хотя токен валиден")
        return jsonify({"success": False, "error": "NOT_FOUND"}), 404

    logger.debug(f"Опрос статуса заказа №{order.id}. Текущий статус в БД: {order.status.value}")
    
    order_details = None
    if order.status == OrderStatus.PAID:
        order_details = {
            "total_amount": order.total_amount / 100,
            "items": [
                {
                    "name": item.product_name,
                    "quantity": item.quantity,
                    "price": item.price_with_discount / 100,
                }
                for item in order.items
            ],
            "delivery_service": order.delivery_service.value,
            "delivery_price": order.delivery_price / 100,
            "customer": {
                "name" : order.customer_name,
                "phone": order.customer_phone,
                "email": order.customer_email
            },
            "created_at": order.created_at.isoformat() 
        }

    return jsonify({
        "success": True, 
        "paid": order.status == OrderStatus.PAID, 
        "order_id": order.id,
        "details": order_details
    }), 200