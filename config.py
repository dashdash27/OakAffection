from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta


env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    DEBUG = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'defaultkeys')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set")
    
    WTF_CSRF_ENABLED = True

    SERVER_NAME = '89.104.74.97:1234'

    # База данных
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("SQLALCHEMY_DATABASE_URI is not set in .env file")
    
    BASE_DIR = Path(__file__).resolve().parent
    STATIC_DIR = BASE_DIR / 'static'
    
    SESSION_COOKIE_SECURE = False        # Только HTTPS
    SESSION_COOKIE_HTTPONLY = True      # Защита от XSS
    SESSION_COOKIE_SAMESITE = 'Strict'  # Максимальная защита CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30) # длительность сессии