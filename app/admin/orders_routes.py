from app.admin.routes import admin_bp 
from app.models import Order


from flask import render_template, request, redirect, url_for, flash


@admin_bp.route('/orders/home', methods=['GET', 'POST'])
def orders_home():
    orders = Order.query.all()
    return render_template('admin/orders/home.html', orders=orders)

@admin_bp.route('/orders/<int:order_id>', methods=['GET', 'POST'])
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/orders/detail.html', order=order)