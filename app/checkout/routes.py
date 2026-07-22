from app.logger import logger
from app.models import Product
from app.extensions import limiter, db
from .utils import process_cart, calculate_order_dimensions, calculate_cart_base_total
from .schemas import OrderCreateSchema 
from .core.order_creator import create_new_order_transaction
from app.payments.services.ozon_pay import request_ozon_pay_link
from app.checkout.core.utils import verify_and_get_delivery_price
from app.checkout.core.utils import validate_order_totals, allocate_items_discount

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
        return jsonify({"success": False, "error": "No data"}), 400
    
    raw_ids = data.get('product_ids', [])

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
        return jsonify({"success": False, "error": "External service error"}), 502
    
    return jsonify(city_suggestions), 200

@checkout_bp.route('/api/delivery/options', methods=['POST'])
@limiter.limit("20 per minute")
async def get_delivery_options():
    req_data = request.get_json()

    if not req_data or 'city_data' not in req_data or 'cart' not in req_data:
        logger.warning("get_delivery_options: Ошибка запроса. Отсутствуют city_data или cart")
        return jsonify({"success": False, "error": "Missing city data"}), 400
    
    city_data = req_data.get('city_data')
    cart = req_data.get('cart')
    
    city_name = city_data.get('value', 'Неизвестный город')
    logger.info(f"Начало расчета вариантов доставки для города: {city_name}")
    
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
        logger.error(f"Глобальный сбой asyncio для Яндекса (city: {city_name}): {yandex_result}", exc_info=True)
        yandex_delivery_info = {
            "status": "tech_error",
            "error_code": "YANDEX_API_DOWN",
            "message": "Служба доставки Яндекса временно недоступна.",
            "points": []
        }
    else:
        yandex_delivery_info = yandex_result

    if isinstance(russian_post_result, Exception):
        logger.error(f"Глобальный сбой asyncio для Почты России (city: {city_name}): {russian_post_result}", exc_info=True)
        russian_post_delivery_info = {
            "status": "tech_error",
            "error_code": "RUSSIAN_POST_API_DOWN",
            "message": "Служба доставки Почты России временно недоступна.",
            "points": []
        }
    else:
        russian_post_delivery_info = russian_post_result

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
    
    print("Прилетели данные для заказа:", raw_data)

    # 1. Validation
    try:
        validated_order = OrderCreateSchema(**raw_data)
    except ValidationError as e:
        print("Ошибки при валидации:", [f"Поле {err['loc']}: {err['msg']}" for err in e.errors()])
        return jsonify({
            "success": False, 
            "error": "Некоторые данные заполнены некорректно. Пожалуйста, проверьте форму."
        }), 422
    
    try:
        # 2. Checking JWT Token
        trusted_delivery_price = verify_and_get_delivery_price(validated_order.delivery.delivery_token)
        
        # 3. Calculate total_amount and compare
        totals_match, order_items, discount_amount, items_discounted_total = validate_order_totals(
            cart=validated_order.cart,
            trusted_delivery_price=trusted_delivery_price,
            client_total_amount=validated_order.client_total_amount
        )
        if not totals_match:
            return jsonify({"success": False, "error": "Ошибка расчета стоимости заказа. Пожалуйста, обновите корзину или выберите ПВЗ заново."}), 422
        
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
        print("Order in DB created:", order.id)

        # 6. Create order in ozon pay
        ozon_pay_cfg = current_app.config.get("OZON_PAY", {})
        pay_link, ext_order_id = request_ozon_pay_link(order, ozon_pay_cfg)

        if pay_link is not None and ext_order_id is not None:
            # 7. Save ext_db for order in DB
            try:
                order.ext_id = ext_order_id  
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({"success": False, "error": "Ошибка сервера при сохранения данных оплаты"}), 500
            
            return jsonify({"success": True, "order_id": order.id, "pay_link": pay_link}), 200
        else:
            return jsonify({"success": False, "error": "Ошибка платежного шлюза"}), 502

    except ValueError as val_err:
        return jsonify({"success": False, "error": str(val_err)}), 422
    except Exception as e:
        print(f"[FATAL ERROR] Критическая ошибка при оформлении: {e}")
        return jsonify({"success": False, "error": "Ошибка сервера при формировании заказа."}), 500