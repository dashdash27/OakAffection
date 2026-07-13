from app.extensions import db

import enum
from sqlalchemy import func


class OrderStatus(enum.Enum):
    PENDING = 'pending'
    PAID = 'paid'
    CANCELLED = 'cancelled'
    SENT = 'sent'
    DELIVERED = 'delivered'
    RETURNED = 'returned'

class DeliveryService(enum.Enum):
    YANDEX = 'yandex'
    RUSSIAN_POST = 'russian_post'


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.BigInteger, primary_key=True)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    customer_name = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)

    delivery_service = db.Column(db.Enum(DeliveryService), nullable=False)
    delivery_settlement = db.Column(db.String(150), nullable=False)
    delivery_point_id = db.Column(db.String(100), nullable=False)
    delivery_point_address = db.Column(db.String(255), nullable=False)
    
    delivery_price = db.Column(db.BigInteger, nullable=False)
    discount_amount = db.Column(db.BigInteger, default=0, nullable=False)
    total_amount = db.Column(db.BigInteger, nullable=False)
    
    created_at = db.Column(
        db.DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    comment = db.Column(db.String(600), default="", nullable=False)
    delivery_track = db.Column(db.String(500), default="", nullable=False)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    payment = db.relationship('Payment', backref='order', uselist=False, lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    
    # ON DELETE SET NULL: если товар удалят через DELETE, id станет NULL, но запись заказа уцелеет
    product_id = db.Column(db.BigInteger, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    
    quantity = db.Column(db.BigInteger, nullable=False)
    
    product_name = db.Column(db.String(255), nullable=False) 
    price_at_purchase = db.Column(db.BigInteger, nullable=False)

    product = db.relationship('Product', lazy=True)