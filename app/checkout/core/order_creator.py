from app.extensions import db
from app.models.order_model import Order, OrderItem, OrderStatus, DeliveryService
from app.models.payment_model import Payment, PaymentStatus, PaymentGateway
from app.logger import logger
from app.checkout.schemas import OrderCreateSchema


def create_new_order_transaction(validated_order: OrderCreateSchema) -> Order:
    """Атомарная транзакция создания заказа в БД.
    
    1. Создает шапку заказа (Order)
    2. Создает чеки (OrderItem)
    3. Создает запись платежа (Payment)
    
    Гарантирует Rollback при любой ошибке.
    """
    logger.debug(f"Старт транзакции БД для создания заказа пользователя {validated_order.client_contacts.email}")

    try:
        # 1. Create Order (Order.status = PENDING) - переводим цены в копейки
        new_order = Order(
            status=OrderStatus.PENDING,

            customer_name=validated_order.client_contacts.name,
            customer_phone=validated_order.client_contacts.phone,
            customer_email=validated_order.client_contacts.email,
            
            delivery_service=DeliveryService(validated_order.delivery.service.lower() or 'yandex'),
            delivery_settlement=validated_order.delivery.settlement.name,
            delivery_point_id=validated_order.delivery.point.id,
            delivery_point_address=validated_order.delivery.point.address,

            delivery_price=int(validated_order.delivery.price * 100),
            discount_amount=int(validated_order.discount_amount * 100),
            total_amount=int(validated_order.total_amount * 100)
        )
        db.session.add(new_order)
        db.session.flush()  # flash to get new_order.id,

        # 2. Create Order Items
        for item in validated_order.order_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item["id"],
                quantity=item["quantity"],
                product_name=item["name"],
                price_at_purchase=int(item["price"] * 100),
                price_with_discount=int(item["price_with_discount"] * 100)
            )
            db.session.add(order_item)

        # 3. Create Payment
        new_payment = Payment(
            order_id=new_order.id,
            gateway=PaymentGateway.OZON,
            amount=new_order.total_amount,
            status=PaymentStatus.PENDING
        )
        db.session.add(new_payment)

        # 4. Fix transaction
        db.session.commit()
        return new_order

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при создании заказа в Ozon Pay.")
        raise e
