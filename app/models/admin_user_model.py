from app.extensions import db
from argon2 import PasswordHasher
from flask_login import UserMixin

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

ph = PasswordHasher()

class AdminUser(db.Model, UserMixin):
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)  # 255 для bcrypt
    
    def set_password(self, password):
        self.password_hash = ph.hash(password)

    def check_password(self, password):
        try:
            return ph.verify(self.password_hash, password)
        except:
            return False
    