from app import create_app
from app.models import AdminUser
from app.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    admin = AdminUser(username='admin')
    admin.set_password('1234')  # ✅ Меняйте на свой!
    db.session.add(admin)
    #AdminUser.query.delete()
    db.session.commit()
    print("✅ Админ создан")