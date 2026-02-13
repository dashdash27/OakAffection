def test_homepage_status(client):
    """Проверяем, что главная страница доступна"""
    result = client.get('/')
    assert result.status_code == 200

def test_404_error(client):
    """Проверка несуществующей страницы"""
    result = client.get('/non-existent-page')
    assert result.status_code == 404

def test_product_detail_page(client):
    app = client.application 
    
    with app.app_context():
        from app.models import Product
        product = Product.query.first()
    
    if product:
        res = client.get(f'/product/{product.slug}')
        assert res.status_code == 200
        assert product.name in res.get_data(as_text=True)

def test_how_to_order_page(client):
    result = client.get('/how-to-order')
    assert result.status_code == 200
