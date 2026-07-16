from config.delivery import DeliveryConfig
from config.geo import GeoConfig
from config.business import BusinessConfig
from config.payments import PaymentsConfig

from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta


env_path = Path(__file__).parent / '.env'
load_dotenv()

class Config(DeliveryConfig, GeoConfig, BusinessConfig, PaymentsConfig):
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1')
    WTF_CSRF_ENABLED = True

    # Secret Key
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set")

    # Data Base
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("SQLALCHEMY_DATABASE_URI is not set in .env file")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    BASE_DIR = Path(__file__).resolve().parent
    STATIC_DIR = BASE_DIR / 'static'
    
    # Security and sessions settings
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1') # local - False, prod - True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax') # local - Lax, prod - Strict
    WTF_CSRF_SSL_STRICT = os.getenv('WTF_CSRF_SSL_STRICT', 'False').lower() in ('true', '1') # local - False, prod - True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)