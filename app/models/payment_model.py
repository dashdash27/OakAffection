from app.extensions import db

import enum
from datetime import datetime, timezone


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
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # onupdate автоматически обновляет время при любом изменении строки
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)