from app.extensions import db, migrate
from app.logger import logger
from app.models import AdminUser
from app.extensions import init_limiter 

from flask_login import LoginManager
from flask import Flask, g, request, render_template
from flask_wtf.csrf import CSRFProtect
import uuid


csrf = CSRFProtect()

def create_app():

    app = Flask(__name__)

    try:
        app.config.from_object('config.Config')

        db.init_app(app)
        migrate.init_app(app, db)
        csrf.init_app(app)

        # 🔒 LoginManager
        # Инициализируем Limiter с app
        init_limiter(app) 

        login_manager = LoginManager()
        login_manager.login_view = "adminlogin.login"  # ✅ Авто-редирект!
        login_manager.init_app(app)              # ✅ Готово!

        @app.errorhandler(429)
        def ratelimit_handler(e):
            return render_template('admin/login.html', ratelimit_error=e.description), 429

        @login_manager.user_loader
        def load_user(user_id):
            return AdminUser.query.get(int(user_id))  # ✅ Готово!

        from app import models  # импорт моделей


        from app.routes import main_bp
        from app.admin.routes import admin_bp, login_bp
        app.register_blueprint(login_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(admin_bp)


        with app.app_context():
            db.create_all()

        @app.before_request
        def assign_request_id():
            g.request_id = str(uuid.uuid4())
            # 🔒 Логирование доступа к админке
            if request.path.startswith('/admin'):
                logger.info(f"Действия админа: {request.remote_addr} -> {request.url}")
        
        logger.info("Приложение успешно запущено")
    except Exception as e:
        logger.error(f"Ошибка при инициализации приложения или подключении к базе: {e}")
        raise

    return app
