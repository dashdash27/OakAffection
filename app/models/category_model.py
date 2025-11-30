from app.extensions import db


products_categories = db.Table(
    'products_categories',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)
product_drafts_categories = db.Table(
    'product_drafts_categories',
    db.Column('product_draft_id', db.Integer, db.ForeignKey('product_drafts.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    description_tag = db.Column(db.Text)
    last_updated = db.Column(db.DateTime(timezone=True))

    products = db.relationship('Product', secondary='products_categories', back_populates='categories')
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

    # drafts
    product_drafts = db.relationship('ProductDraft', secondary='product_drafts_categories', back_populates='categories')

    def __str__(self):
        return self.name
    
