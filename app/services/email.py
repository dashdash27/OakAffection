from app.models import Order
from app.logger import logger

import smtplib
import os
from concurrent.futures import ThreadPoolExecutor
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app, render_template

email_executor = ThreadPoolExecutor(max_workers=2)

def _sync_send_smtp(to_email, subject, html_body):
    """
    Внутренняя функция. Выполняется изолированно в фоновом потоке.
    Занимается реальной отправкой почты через SMTP.
    """
    smtp_server = current_app.config.get("MAIL_SERVER", "smtp.yandex.ru")
    smtp_port = current_app.config.get("MAIL_PORT", 465)
    smtp_user = current_app.config.get("MAIL_USERNAME")
    smtp_password = current_app.config.get("MAIL_PASSWORD")
    sender_email = smtp_user

    if not smtp_user or not smtp_password:
        logger.warning("[ФОН] Ошибка отправки почты: Не настроены MAIL_USERNAME или MAIL_PASSWORD в config.")
        return

    # Префикс
    email_prefix = current_app.config.get("EMAIL_PREFIX", "")

    # Формируем структуру письма (поддерживает HTML и кириллицу)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{email_prefix}{subject}"
    msg["From"] = sender_email
    msg["To"] = to_email

    # Добавляем копию письма
    msg["Bcc"] = sender_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        logger.debug(f"[ФОН] Попытка отправки SMTP-пакета на адрес: {to_email}")
        
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, [to_email, sender_email], msg.as_string())
            
        logger.info(f"[ФОН] Письмо успешно отправлено на {to_email} (Тема: {subject})")
        
    except smtplib.SMTPException as smtp_err:
        logger.error(f"[ФОН] Сбой SMTP при отправке письма на {to_email}. Ошибка: {smtp_err}")
        
    except Exception:
        logger.exception(f"[ФОН] Непредвиденая ошибка при отправке письма на {to_email}")


# --- Публичные функции --- 
def send_order_confirmation_email(to_email, order_id):
    """
    Тип 1: Письмо об успешной оплате заказа с деталями.
    Принимает email клиента и id заказа.
    """
    logger.debug(f"Инициализация фоновой отправки письма-подтверждения для заказа №{order_id}")

    app = current_app._get_current_object()
    def _prepare_and_send():
        # Этот код выполнится уже изнутри потока, где активен app_context
        with app.app_context():
            try:
                order = Order.query.get(order_id)
                if not order:
                    logger.warning(f"[ФОН] Заказ №{order_id} не найден в БД. Отмена отправки письма-подтверждения.")
                    return

                subject = f"Заказ №{order.id} успешно оплачен"

                html_body = render_template(
                    'emails/order_email.html', 
                    type='paid',
                    subject=subject,
                    order=order
                )
                
                # Вызываем отравку
                _sync_send_smtp(to_email, subject, html_body)

            except Exception:
                logger.exception(f"[ФОН] Критический сбой при подготовке письма подтверждения для заказа №{order_id}")

    # Закидываем в пул внутреннюю функцию-обертку
    email_executor.submit(_prepare_and_send)

def send_delivery_track_email(to_email, order_id):
    """
    Тип 2: Письмо с трек номером заказа.
    Принимает email клиента и id заказа.
    """
    logger.debug(f"Инициализация фоновой отправки письма с трек-номером для заказа №{order_id}")

    app = current_app._get_current_object()
    def _prepare_and_send():
        with app.app_context():
            try:
                order = Order.query.get(order_id)
                if not order:
                    logger.warning(f"[ФОН] Заказ №{order_id} не найден в БД. Отмена отправки письма с трек-номером.")
                    return

                subject = f"Ваш заказ №{order.id} отправлен! Трек-номер внутри"

                html_body = render_template(
                    'emails/order_email.html', 
                    type='track',
                    subject=subject,
                    order=order
                )
                
                _sync_send_smtp(to_email, subject, html_body)
            except Exception:
                logger.exception(f"[ФОН] Критический сбой при подготовке письма с трек-номером для заказа №{order_id}")
            
    # Закидываем в пул внутреннюю функцию-обертку
    email_executor.submit(_prepare_and_send)