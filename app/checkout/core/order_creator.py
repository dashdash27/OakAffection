from app.extensions import db
from app.models.order_model import Order, OrderItem, OrderStatus, DeliveryService
from app.models.payment_model import Payment, PaymentStatus, PaymentGateway
from app.models.product_model import Product
from app.checkout.schemas import OrderCreateSchema


def create_new_order_transaction(validated_order: OrderCreateSchema) -> Order:
    """Атомарная транзакция создания заказа в БД.
    
    1. Создает шапку заказа (Order)
    2. Извлекает из БД актуальные цены и названия товаров и создает чеки (OrderItem)
    3. Создает запись платежа (Payment)
    
    Гарантирует Rollback при любой ошибке.
    """
    try:
        # 1. Create Order (Order.status = PENDING)
        new_order = Order(
            status=OrderStatus.PENDING,

            customer_name=validated_order.client_contacts.name,
            customer_phone=validated_order.client_contacts.phone,
            customer_email=validated_order.client_contacts.email,
            
            delivery_service=DeliveryService(validated_order.delivery.service.lower() or 'yandex'),
            delivery_settlement=validated_order.delivery.settlement.name,
            delivery_point_id=validated_order.delivery.point.id,
            delivery_point_address=validated_order.delivery.point.address,
            
            # TODO: вот эту цену проверять на фронте, чтобы она с trusted совпадала - в том файле проверку сделать
            delivery_price=validated_order.delivery.price,
            discount_amount=validated_order.discount_amount,
            total_amount=validated_order.total_amount
        )
        db.session.add(new_order)
        
        # 2. Flash to get new_order.id,
        db.session.flush()

        # 3. Get all products IDs
        product_ids = [int(pid) for pid in validated_order.cart.keys()]
        
        # 4. Get all products
        db_products = Product.query.filter(Product.id.in_(product_ids)).all()
        products_lookup = {p.id: p for p in db_products}

        # 5. Create Order Items
        for product_id_str, quantity in validated_order.cart.items():
            pid_int = int(product_id_str)
            product_obj = products_lookup.get(pid_int)
            
            if not product_obj:
                # На всякий случай: если товар удалили из каталога прямо в секунду оформления
                raise ValueError(f"Товар с ID {pid_int} больше недоступен в каталоге.")

            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product_obj.id,
                quantity=quantity,
                product_name=product_obj.name,
                price_at_purchase=product_obj.price
            )
            db.session.add(order_item)

        # 6. Create Payment
        new_payment = Payment(
            order_id=new_order.id,
            gateway=PaymentGateway.OZON,
            amount=new_order.total_amount,
            status=PaymentStatus.PENDING
        )
        db.session.add(new_payment)

        # 7. Fix transaction
        db.session.commit()
        return new_order

    except Exception as e:
        db.session.rollback()
        print(f"[CORE ERROR] Ошибка создания транзакции заказа: {e}")
        raise e
