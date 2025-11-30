from app.extensions import db


class Characteristic(db.Model):
    __tablename__ = 'characteristics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    product_characteristics = db.relationship('ProductCharacteristic', back_populates='characteristic')
    groups = db.relationship('ProductGroup', back_populates='characteristic')

    # draft
    product_draft_characteristics = db.relationship('ProductDraftCharacteristic', back_populates='characteristic')

    def __str__(self):
        return self.name

class ProductCharacteristic(db.Model):
    __tablename__ = 'products_characteristics'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    characteristic_id = db.Column(db.Integer, db.ForeignKey('characteristics.id'))
    value = db.Column(db.Text)

    product = db.relationship('Product', back_populates='characteristics')
    characteristic = db.relationship('Characteristic', back_populates='product_characteristics')

class ProductDraftCharacteristic(db.Model):
    __tablename__ = 'product_drafts_characteristics'

    id = db.Column(db.Integer, primary_key=True)
    product_draft_id = db.Column(db.Integer, db.ForeignKey('product_drafts.id'))
    characteristic_id = db.Column(db.Integer, db.ForeignKey('characteristics.id'))
    value = db.Column(db.Text)

    product_draft = db.relationship('ProductDraft', back_populates='characteristics')
    characteristic = db.relationship('Characteristic', back_populates='product_draft_characteristics')
