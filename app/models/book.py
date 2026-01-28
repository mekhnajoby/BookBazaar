from app import db
from datetime import datetime


class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    genre = db.Column(db.String(100), nullable=True)
    publisher = db.Column(db.String(150), nullable=True)
    publication_date = db.Column(db.Date, nullable=True)
    isbn = db.Column(db.String(20), unique=True, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='book', lazy='dynamic')
    cart_items = db.relationship('CartItem', backref='book', lazy='dynamic')
    
    def is_in_stock(self):
        return self.stock_quantity > 0
    
    def reduce_stock(self, quantity):
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            return True
        return False
    
    def __repr__(self):
        return f'<Book {self.title}>'
