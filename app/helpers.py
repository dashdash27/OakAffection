from app.models import Product, Category, products_categories

def get_category_path(category):
    path = []
    current = category
    while current is not None:
        path.append(current)
        current = current.parent
    path.reverse()
    return path

def get_all_descendants(category):
    descendants = []

    def _recurse(cat):
        if cat:
            for child in cat.children:
                descendants.append(child)
                _recurse(child)

    _recurse(category)
    return descendants

def get_products_by_category(category_name):
    category = Category.query.filter_by(name=category_name).first()

    categories = [category] + get_all_descendants(category)
    categories = [cat for cat in categories if cat is not None]
    category_ids = []
    if categories:
        category_ids = [cat.id for cat in categories]

    products = Product.query.join(products_categories).filter(
        products_categories.c.category_id.in_(category_ids)
    ).order_by(Product.name.asc()).all()

    return products
