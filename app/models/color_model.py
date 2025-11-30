from app.extensions import db


class Color(db.Model):
    __tablename__ = 'colors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    icon_url = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('color_categories.id'))
    
    category = db.relationship('ColorCategory', back_populates='colors')
    products = db.relationship('Product', back_populates='color')

    product_drafts = db.relationship('ProductDraft', back_populates='color')

    def __str__(self):
        return self.name
