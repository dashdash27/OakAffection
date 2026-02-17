from app.logger import logger
from app.models import Product
from app.extensions import STATIC_DIR

import os
from flask import Blueprint, render_template, request, jsonify

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

@checkout_bp.route('/cart')
def cart():
    return render_template('checkout/cart.html')


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
        result.append({
            "id": p.id,
            "name": p.name,
            "price": int(p.price) if p.price else None,
            "photo_path": f"/static/{p.photos[0].photo_url}" if p.photos[0] else None
        })
    
    return jsonify(result), 200