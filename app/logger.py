import logging
from logging.handlers import RotatingFileHandler
from flask import g, has_request_context
import os

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            # Если контекст запроса активен — берем request_id из g
            record.request_id = getattr(g, 'request_id', 'no-request-id')
        else:
            # Если контекста нет — ставим дефолтное значение
            record.request_id = 'no-request-id'
        return True

def setup_logger():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    logger = logging.getLogger('myapp')

    is_debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1')

    if is_debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.propagate = False  # предотвращаем дублирование

    formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(request_id)s] %(message)s')

    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Добавляем обработчики только если их еще нет
    if logger.hasHandlers():
        logger.handlers.clear()

    # --- ОБРАБОТЧИК 1: ЗАПИСЬ В ФАЙЛ ---
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'), 
        maxBytes=10*1024*1024, 
        backupCount=5, 
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(RequestIdFilter())
    logger.addHandler(file_handler)

    # --- ОБРАБОТЧИК 2: ВЫВОД В КОНСОЛЬ ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    console_handler.addFilter(RequestIdFilter())
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()