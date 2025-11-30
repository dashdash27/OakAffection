from app.extensions import db


class ColorCategory(db.Model):
    __tablename__ = 'color_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    colors = db.relationship('Color', back_populates='category', cascade='all, delete-orphan')

    def __str__(self):
        return self.name