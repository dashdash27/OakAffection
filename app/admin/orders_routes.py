from app.admin.routes import admin_bp 
from app.models import Order, OrderStatus


from flask import render_template, request, redirect, url_for, flash


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
    return render_template('admin/orders/detail.html', order=order)