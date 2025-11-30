from app.extensions import db


class ProductVideo(db.Model):
    __tablename__ = 'products_videos'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    video_url = db.Column(db.Text)
    sort_index = db.Column(db.Integer, nullable=True, default=0)

    product = db.relationship('Product', back_populates='videos')


class ProductDraftVideo(db.Model):
    __tablename__ = 'product_drafts_videos'

    id = db.Column(db.Integer, primary_key=True)
    product_draft_id = db.Column(db.Integer, db.ForeignKey('product_drafts.id'))
    video_url = db.Column(db.Text)
    sort_index = db.Column(db.Integer, nullable=True, default=0)

    product_draft = db.relationship('ProductDraft', back_populates='videos')
