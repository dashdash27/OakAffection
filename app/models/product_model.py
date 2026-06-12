from app.extensions import db

from sqlalchemy import Column, DateTime, func


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)
    application = db.Column(db.Text)
    is_new = db.Column(db.Boolean, default=False)
    ozon_link = db.Column(db.Text)
    wb_link = db.Column(db.Text)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('product_groups.id'), nullable=True)
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'), nullable=True)
    description_tag = db.Column(db.Text)
    delete_mark = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    weight = db.Column(db.Integer, nullable=True)

    # wrapper
    wrapper_id = db.Column(db.Integer, db.ForeignKey('product_wrappers.id'), nullable=True)
    wrapper = db.relationship('ProductWrapper', backref='products')

    # draft
    draft = db.relationship('ProductDraft', back_populates='product', uselist=False)

    # отношения
    photos = db.relationship('ProductPhoto', back_populates='product', cascade='all, delete-orphan', order_by='ProductPhoto.sort_index')
    videos = db.relationship('ProductVideo', back_populates='product', cascade='all, delete-orphan')
    characteristics = db.relationship('ProductCharacteristic', back_populates='product', cascade='all, delete-orphan')
    categories = db.relationship('Category', secondary='products_categories', back_populates='products')
    targets = db.relationship('Target', secondary='products_targets', back_populates='products')
    group = db.relationship('ProductGroup', back_populates='products')
    color = db.relationship('Color', back_populates='products')

    def __str__(self):
        return self.name
    
class ProductDraft(db.Model):
    __tablename__ = 'product_drafts'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    name = db.Column(db.String(255))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)
    application = db.Column(db.Text)
    is_new = db.Column(db.Boolean, default=False)
    ozon_link = db.Column(db.Text)
    wb_link = db.Column(db.Text)
    slug = db.Column(db.String(255), unique=True)
    group_id = db.Column(db.Integer, db.ForeignKey('product_groups.id'))
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'))
    description_tag = db.Column(db.Text)
    weight = db.Column(db.Integer, nullable=True)

    # wrapper
    wrapper_id = db.Column(db.Integer, db.ForeignKey('product_wrappers.id'), nullable=True)
    wrapper = db.relationship('ProductWrapper', backref='product_drafts')

    product = db.relationship('Product', back_populates='draft')

    # отношения
    photos = db.relationship('ProductDraftPhoto', back_populates='product_draft', cascade='all, delete-orphan', order_by='ProductDraftPhoto.sort_index')
    videos = db.relationship('ProductDraftVideo', back_populates='product_draft', cascade='all, delete-orphan')
    characteristics = db.relationship('ProductDraftCharacteristic', back_populates='product_draft', cascade='all, delete-orphan')
    categories = db.relationship('Category', secondary='product_drafts_categories', back_populates='product_drafts')
    targets = db.relationship('Target', secondary='product_drafts_targets', back_populates='product_drafts')
    group = db.relationship('ProductGroup', back_populates='product_drafts')
    color = db.relationship('Color', back_populates='product_drafts')

    def __str__(self):
        return self.name
