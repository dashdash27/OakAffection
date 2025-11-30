from app.extensions import db


products_targets = db.Table(
    'products_targets',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('target_id', db.Integer, db.ForeignKey('targets.id'), primary_key=True)
)

product_draft_targets = db.Table(
    'product_drafts_targets',
    db.Column('product_draft_id', db.Integer, db.ForeignKey('product_drafts.id'), primary_key=True),
    db.Column('target_id', db.Integer, db.ForeignKey('targets.id'), primary_key=True)
)

class Target(db.Model):
    __tablename__ = 'targets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    products = db.relationship('Product', secondary='products_targets', back_populates='targets')
    product_drafts = db.relationship('ProductDraft', secondary='product_drafts_targets', back_populates='targets')

    def __str__(self):
        return self.name
    