from flask import Blueprint, render_template, abort
from app.models import Product, Category, ProductCharacteristic
from app.helpers import get_products_by_category

main_bp = Blueprint('main', __name__)

categories_dict = {
    'oils': 'Масла для обработки дерева',
    'indoor_oils': 'Масла для внутренних работ',
    'outdoor_oils': 'Масла для наружных работ',
    'other_oils': 'Другие масла',
    'kitchen_oils': 'Масла для кухонной утвари',
    'furniture_oils': 'Масла для мебели',
    'toy_oils': 'Масла для игрушек',
    'bath_oils': 'Масла для бань и саун',
    'terrace_oils': 'Масла для террас',
    'garden_furniture_oils': 'Масла для садовой мебели',
    'facade_oils': 'Масла для фасадов',
    'tinted_oils': 'Колерованные масла',
    'liquids': 'Грунтовочные масла и растворители'
}


@main_bp.route('/')
def index():
    new_products = Product.query.filter(Product.is_new == True).all()
    return render_template('index.html', new_products=new_products)

@main_bp.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    if not product:
        abort(404)

    product_group_characteristic_value = None
    sorted_group_products = None
    
    if product.group:
        characteristic_id = product.group.characteristic.id

        product_group_characteristic = ProductCharacteristic.query.filter_by(
            product_id=product.id, characteristic_id=characteristic_id
        ).first()
        product_group_characteristic_value = product_group_characteristic.value

        # сортируем товары группы по значению характеристики группы: 200ml, 1000ml...
        def extract_digit_value(s):
            # Извлекаем число из строки, например, '200 ml' -> 200
            return int(''.join(filter(str.isdigit, s)))

        if product.group.characteristic.name == "Объем":
            sorted_group_products = sorted(
                product.group.products,
                key=lambda p: extract_digit_value(
                    next((c.value for c in p.characteristics if c.characteristic_id == characteristic_id), '0')
                )
            )
        else:
            sorted_group_products = sorted(
                product.group.products,
                key=lambda p: next((c.value for c in p.characteristics if c.characteristic_id == characteristic_id), '0')
            )
    

    return render_template(
        'product_detail.html', 
        product=product, 
        product_group_characteristic_value=product_group_characteristic_value,
        sorted_group_products=sorted_group_products
    )


@main_bp.route('/<category_key>')
def show_oils(category_key):
    category_name = categories_dict.get(category_key)
    category = Category.query.filter_by(name=category_name).first()
    if not category:
        abort(404)
    
    products = get_products_by_category(category_name)

    return render_template(
        'oils.html',
        products=products,
        category=category
    )

@main_bp.route('/how-to-order')
def how_to_order():
    return render_template('how_to_order.html')