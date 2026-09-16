import os
import sys
from flask import Flask
from dotenv import load_dotenv
from pathlib import Path

# 1. Настраиваем пути, чтобы Python гарантированно видел пакет 'app' из корня проекта.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. Подгружаем env
env_path = Path(project_root) / '.env'
load_dotenv(dotenv_path=env_path)

# 3. Импортируем конфиг.
from config import Config

# 4. Импортируем логгер и функцию-запуск
from app.logger import logger
from app.checkout.services.ozon_delivery.cron_worker import run_full_pickup_points_sync

def create_lightweight_cron_app():
    """Создает легковесное Flask-приложение специально для конфигурации Крона."""
    app = Flask(__name__)
    try:
        app.config.from_object(Config)
    except Exception as e:
        logger.error(f"[Cron Ozon Delivery] Не удалось загрузить конфигурацию config.Config: {e}")
        sys.exit(1)

    logger.info("[Cron Ozon Delivery] Приложение создано. Конфигурация успешно загружена.")
    return app

def main():
    logger.info("[Cron Ozon Delivery] Создание легковесного приложения для фоновой задачи...")
    
    # Инициализируем легкое приложение без CSRF, LoginManager и лишних роутов
    cron_app = create_lightweight_cron_app()
    
    # Входим в контекст приложения Flask
    with cron_app.app_context():
        run_full_pickup_points_sync()

if __name__ == "__main__":
    main()