from app.logger import logger
from app.models import Product
from app.extensions import limiter
from .utils import calculate_order_dimensions, calculate_order_price

from .services.dadata import get_city_suggestions
from .services.yandex import get_yandex_delivery_info, get_fake_delivery_info
from .services.russian_post import get_russian_post_delivery_info

import asyncio
import httpx
import json
from flask import Blueprint, render_template, request, jsonify

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

@checkout_bp.route('/cart')
def cart():
    return render_template('checkout/cart.html')

@checkout_bp.route('/checkout')
def checkout():
    return render_template('checkout/checkout.html')

@checkout_bp.route('/api/suggestions/cities', methods=['GET'])
@limiter.limit("30 per minute")
def suggest_cities():
    query = request.args.get('q', '').strip()
    
    if len(query) < 3:
        return jsonify([]), 200
    
    city_suggestions = get_city_suggestions(query)

    if city_suggestions is None:
        return jsonify({"success": False, "error": "External service error"}), 502
    
    return jsonify(city_suggestions), 200

def process_cart(cart):
    clean_ids = []
    for pid in cart.keys():
        try:
            clean_ids.append(int(pid))
        except (ValueError, TypeError):
            continue
    
    products = Product.query.filter(Product.id.in_(clean_ids)).all()

    # TODO: add actual weights and params after migrations
    order_items = []
    for p in products:
        order_items.append({
            "id": p.id,
            "name": p.name,
            "quantity": cart.get(str(p.id)) or cart.get(p.id),
            "price": p.price,
            "weight": 500,
            "length": 10,
            "height": 10,
            "depth": 10
        })

    return order_items

@checkout_bp.route('/api/delivery/options', methods=['POST'])
@limiter.limit("20 per minute")
async def get_delivery_options():
    req_data = request.get_json()
    if not req_data or 'city_data' not in req_data or 'cart' not in req_data:
        return jsonify({"success": False, "error": "Missing city data"}), 400
    
    print(("Delivery options request..."))
    
    city_data = req_data.get('city_data')
    cart = req_data.get('cart')

    order_items = process_cart(cart)
    order_dimensions = calculate_order_dimensions(order_items)
    order_price = calculate_order_price(order_items)

    print("--- ORDER INPUT DATA ---")
    print("City:\n", json.dumps(city_data, indent=4, ensure_ascii=False))
    print("Order dims:\n", json.dumps(order_dimensions, indent=4, ensure_ascii=False))
    print("Order price:", order_price)
    print("--------------------------------------")

    # Create 1 client for all requests of this user
    async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
        tasks = [
            get_yandex_delivery_info(city_data, order_dimensions, client),
            get_russian_post_delivery_info(city_data, order_dimensions, order_price, client)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
    yandex_result = results[0]
    russian_post_result = results[1]
    
    if isinstance(yandex_result, Exception):
        print(f"Критическое системное исключение в asyncio.gather для Яндекса: {yandex_result}")
        yandex_delivery_info = {
            "status": "tech_error",
            "error_code": "YANDEX_API_DOWN",
            "message": "Служба доставки Яндекса временно недоступна.",
            "points": []
        }
    else:
        yandex_delivery_info = yandex_result

    if isinstance(russian_post_result, Exception):
        print(f"Критическое системное исключение в asyncio.gather для Почты России: {russian_post_result}")
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
    
    if not clean_ids:
        return jsonify([]), 200
    
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
    
    return jsonify(result), 200