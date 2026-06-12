from app.extensions import db

class ProductWrapper(db.Model):
    __tablename__ = 'product_wrappers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    length = db.Column(db.Integer, nullable=False)   # cm
    height = db.Column(db.Integer, nullable=False)   # cm
    depth = db.Column(db.Integer, nullable=False)    # cm