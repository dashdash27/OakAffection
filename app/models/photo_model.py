from app.extensions import db

class ProductPhoto(db.Model):
    __tablename__ = 'products_photos'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    photo_url = db.Column(db.Text)
    alt = db.Column(db.Text)
    sort_index = db.Column(db.Integer, nullable=True, default=0)

    product = db.relationship('Product', back_populates='photos')

class ProductDraftPhoto(db.Model):
    __tablename__ = 'product_drafts_photos'

    id = db.Column(db.Integer, primary_key=True)
    product_draft_id = db.Column(db.Integer, db.ForeignKey('product_drafts.id'))
    photo_url = db.Column(db.Text)
    alt = db.Column(db.Text)
    sort_index = db.Column(db.Integer, nullable=True, default=0)

    product_draft = db.relationship('ProductDraft', back_populates='photos')
