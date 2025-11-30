from app.extensions import db


class ProductGroup(db.Model):
    __tablename__ = 'product_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    characteristic_id = db.Column(db.Integer, db.ForeignKey('characteristics.id'), nullable=True)
    characteristic = db.relationship('Characteristic', back_populates='groups', uselist=False)

    products = db.relationship('Product', back_populates='group')
    product_drafts = db.relationship('ProductDraft', back_populates='group')


    def __str__(self):
        return self.name
    
    # @property
    # def original_characteristics(self):
    #     return self._original_characteristics or []

    # @original_characteristics.setter
    # def original_characteristics(self, value):
    #     self._original_characteristics = value