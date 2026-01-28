from app import db
from datetime import datetime


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    books = db.relationship('Book', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.category_name}>'
