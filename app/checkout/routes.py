from app.logger import logger
from app.models import Product
from .utils import calculate_order_dimensions

from .services.dadata import get_city_suggestions
from .services.yandex import get_yandex_delivery_info, get_fake_delivery_info

import asyncio
import httpx
from flask import Blueprint, render_template, request, jsonify

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

@checkout_bp.route('/cart')
def cart():
    return render_template('checkout/cart.html')

@checkout_bp.route('/checkout')
def checkout():
    return render_template('checkout/checkout.html')

@checkout_bp.route('/api/suggestions/cities', methods=['GET'])
def suggest_cities():
    query = request.args.get('q', '').strip()
    
    if len(query) < 3:
        return jsonify([]), 200
    
    city_suggestions = get_city_suggestions(query)

    if city_suggestions is None:
        return jsonify({"success": False, "error": "External service error"}), 502
    
    return jsonify(city_suggestions), 200

def process_cart(cart):
    product_ids = list(cart.keys())

    # валидация ids
    # TODO: create outer function to clean
    clean_ids = []
    for pid in product_ids:
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
            "quantity": cart[str(p.id)],
            "weight": 500,
            "length": 20,
            "height": 20,
            "depth": 10
        })

    return order_items

@checkout_bp.route('/api/delivery/options', methods=['POST'])
async def get_delivery_options():
    req_data = request.get_json()
    if not req_data or 'city_data' not in req_data or 'cart' not in req_data:
        return jsonify({"success": False, "error": "Missing city data"}), 400
    
    city_data = req_data.get('city_data')
    print("City_data", city_data)
    cart = req_data.get('cart')

    order_items = process_cart(cart)
    print("Order_items", order_items)

    order_dimensions = calculate_order_dimensions(order_items)
    print("Order_dimensions", order_dimensions)

    # Create 1 client for all requests of this user
    async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
        tasks = [
            get_yandex_delivery_info(city_data, order_dimensions, client)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
    valid_options = [res for res in results if res and not isinstance(res, Exception)]


    if not valid_options:
        return jsonify({"success": False, "error": "External service error"}), 502
    
    yandex_delivery_info = valid_options[0]
    
    results = {}

    if yandex_delivery_info:
        results['yandex'] = {
        "name": "Яндекс Доставка",
        "price": yandex_delivery_info.get('price'),
        "days": yandex_delivery_info.get('delivery_days'),
        "geo_id": yandex_delivery_info.get('geo_id'), 
        "points": yandex_delivery_info.get('points') 
    }

    results['post'] = {
        "name": "Почта России",
        "price": 350,
        "days": "1-2 дня",
        "points": [
            {"id": "y1", "address": "ул. Персиковая, 10", "coords": [45.0, 38.9]},
            {"id": "y2", "address": "ул. Пальмовая, 120", "coords": [45.0, 38.9]}
        ]
    }
    
    return jsonify(results), 200


@checkout_bp.route('/api/cart/sync', methods=['POST'])
def sync_cart():
    data = request.get_json()
    if not data or 'product_ids' not in data:
        return jsonify({"success": False, "error": "No data"}), 400
    
    raw_ids = data.get('product_ids', [])

    # валидация ids
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