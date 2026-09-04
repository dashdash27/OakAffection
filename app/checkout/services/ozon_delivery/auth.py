from app.logger import logger
import sqlite3
import time
import requests
import httpx 

def get_cached_token_or_none(db_path: str) -> str | None:
    """Читает токен из хэша и проверяет его дату истечения."""
    conn = sqlite3.connect(db_path, timeout=3.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT token, expires_at FROM api_tokens WHERE name = 'ozon_delivery_access_token'"
        )
        row = cursor.fetchone()
    except Exception as e:
        logger.error(f"[Ozon Delivery Auth] Ошибка при чтении токена из БД: {e}")
        row = None
    finally:
        conn.close()
        
    if row:
        token, expires_at = row[0], row[1]
        current_time = int(time.time())
        if expires_at - current_time > 300:
            return token
            
    return None


def save_token_to_cache(db_path: str, token: str, expires_at: int):
    """Записывает обновленный токен в кэш."""
    conn = sqlite3.connect(db_path, timeout=3.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_tokens (name, token, expires_at)
            VALUES ('ozon_delivery_access_token', ?, ?)
            ON CONFLICT(name) DO UPDATE SET token=excluded.token, expires_at=excluded.expires_at
        """, (token, expires_at))
        conn.commit()
    except Exception as e:
        logger.error(f"[Ozon DeliveryAuth] Ошибка при сохранении токена в БД: {e}")
        raise
    finally:
        conn.close()

def get_valid_access_token_sync(ozon_delivery_cfg: dict) -> str:
    """Синхронная функция для Крона."""
    db_path = ozon_delivery_cfg.get("DB_PATH")

    # Ищем токен в кэше
    cached_token = get_cached_token_or_none(db_path)
    if cached_token:
        logger.info("[Cron Ozon Delivery]: Токен взят из хэша и действителен.")
        return cached_token

    logger.info("[Cron Ozon Delivery]: Токен устарел. Запрашиваем новый...")

    client_id = ozon_delivery_cfg.get("API_CLIENT_ID")
    client_secret = ozon_delivery_cfg.get("API_CLIENT_SECRET")
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": ["delivery-api.all"]
    }
    
    response = requests.post(ozon_delivery_cfg.get("URL_ACCESS_TOKEN"), json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()

    new_token = data.get("access_token")
    expires_at = int(data.get("expires_in"))

    try:
        save_token_to_cache(db_path, new_token, expires_at)
    except Exception as e:
        logger.warning(f"[Cron Ozon Delivery]: Ошибка при сохранении токена в БД: {e}")

    return new_token

async def get_valid_access_token_async(client: httpx.AsyncClient, ozon_delivery_cfg: dict) -> str:
    """Асинхронная функция для Flask чекаута. Работает внутри asyncio.gather."""
    db_path = ozon_delivery_cfg.get("DB_PATH")

    cached_token = get_cached_token_or_none(db_path)
    if cached_token:
        logger.info("[Ozon Delivery]: Токен взят из хэша и действителен.")
        return cached_token

    logger.info("[Ozon Delivery]: Токен устарел. Запрашиваем новый...")
    
    payload = {
        "client_id": ozon_delivery_cfg.get("API_CLIENT_ID"),
        "client_secret": ozon_delivery_cfg.get("API_CLIENT_SECRET"),
        "grant_type": "client_credentials",
        "scope": ["delivery-api.all"]
    }
    
    # Чистый асинхронный запрос через ваш сессионный client
    response = await client.post(ozon_delivery_cfg.get("URL_ACCESS_TOKEN"), json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()

    new_token = data.get("access_token")
    expires_at = int(data.get("expires_in"))

    try:
        save_token_to_cache(db_path, new_token, expires_at)
    except Exception as e:
        logger.warning(f"[Ozon Delivery]: Ошибка при сохранении токена в БД: {e}")

    return new_token
