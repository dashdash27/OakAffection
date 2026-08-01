from app.models import Order

import smtplib
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
    print("Фон: Начало отправки письма _...")

    smtp_server = current_app.config.get("MAIL_SERVER", "smtp.yandex.ru")
    smtp_port = current_app.config.get("MAIL_PORT", 465)
    smtp_user = current_app.config.get("MAIL_USERNAME")
    smtp_password = current_app.config.get("MAIL_PASSWORD")
    sender_email = smtp_user

    if not smtp_user or not smtp_password:
        print("Фон: Ошибка отправки. Не настроены MAIL_USERNAME или MAIL_PASSWORD в config.")
        return

    # Формируем структуру письма (поддерживает HTML и кириллицу)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    # Добавляем копию письма
    msg["Bcc"] = sender_email

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        print(f"Фон: Попытка отправки письма для {to_email}...")
        
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, [to_email, sender_email], msg.as_string())
            
        print(f"Фон: Письмо успешно отправлено на {to_email}")
        
    except smtplib.SMTPConnectError:
        print(f"Фон: Ошибка подключения к SMTP серверу {smtp_server}")
    except smtplib.SMTPAuthenticationError:
        print("Фон: Ошибка авторизации в SMTP. Проверьте логин или пароль приложения почты.")
    except Exception as e:
        print(f"Фон: Непредвиденная ошибка при отправке на {to_email}: {e}",)


# --- Публичные функции --- 
def send_order_confirmation_email(to_email, order_id):
    """
    Тип 1: Письмо об успешной оплате заказа с деталями.
    Принимает email клиента и id заказа.
    """
    print("Фон: Начало отправки письма confirm...")
    app = current_app._get_current_object()
    def _prepare_and_send():
        # Этот код выполнится уже ИЗНУТРИ потока, где активен app_context
        # Находим заказ в БД. get() автоматически подтянет данные
        with app.app_context():
            order = Order.query.get(order_id)
            if not order:
                print(f"Фон: Заказ №{order_id} не найден в БД для отправки письма.")
                return

            subject = f"Заказ №{order.id} успешно оплачен"
            
            # Передаем объект модели напрямую в шаблонизатор Jinja2
            html_body = render_template(
                'emails/order_email.html', 
                type='paid',
                subject=subject,
                order=order
            )
            
            # Вызываем отпвку
            _sync_send_smtp(to_email, subject, html_body)

    # Закидываем в пул внутреннюю функцию-обертку
    email_executor.submit(_prepare_and_send)

def send_delivery_track_email(to_email, order_id):
    """
    Тип 2: Письмо с трек номером заказа.
    Принимает email клиента и id заказа.
    """
    print("Фон: Начало отправки письма track...")
    app = current_app._get_current_object()
    def _prepare_and_send():
        with app.app_context():
            order = Order.query.get(order_id)
            if not order:
                print(f"Фон: Заказ №{order_id} не найден в БД для отправки письма с трек номером.")
                return

            subject = f"Ваш заказ №{order.id} отправлен! Трек-номер внутри"
            
            # Передаем объект модели напрямую в шаблонизатор Jinja2
            html_body = render_template(
                'emails/order_email.html', 
                type='track',
                subject=subject,
                order=order
            )
            
            # Вызываем отпвку
            _sync_send_smtp(to_email, subject, html_body)

    # Закидываем в пул внутреннюю функцию-обертку
    email_executor.submit(_prepare_and_send)