from flask import Blueprint

# 1. Создаем блюпринт строго ЗДЕСЬ
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
login_bp = Blueprint('adminlogin', __name__, url_prefix='/adminlogin')

# 2. 🔥 Импортируем роуты в самом низу, когда объект admin_bp уже гарантированно создан в памяти
from app.admin import routes
from app.admin import orders_routes