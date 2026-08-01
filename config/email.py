import os

class EmailConfig:
    MAIL_SERVER = "smtp.mail.ru"
    MAIL_PORT = 465
    MAIL_USERNAME = "shop@oakaffection.ru"
    MAIL_DEFAULT_SENDER = '"Интернет-магазин Oak Affection" <shop@oakaffection.ru>'
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")