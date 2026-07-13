from app.extensions import db

import enum
from sqlalchemy import func


class PaymentStatus(enum.Enum):
    PENDING = 'pending'
    REJECTED = 'rejected'
    COMPLETED = 'completed'

class PaymentGateway(enum.Enum):
    OZON = 'ozon'

class Payment(db.Model):
    """Таблица платежей, привязанных к заказам."""
    __tablename__ = 'payments'
    
    id = db.Column(db.BigInteger, primary_key=True)
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    gateway = db.Column(db.Enum(PaymentGateway), default=PaymentGateway.OZON, nullable=False)
    external_id = db.Column(db.String(255), default="", nullable=False) # ID платежной сессии от платежной системы
    amount = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    created_at = db.Column(
        db.DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )