from app import db
from datetime import datetime


class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_total(self):
        return sum(item.quantity * item.book.price for item in self.items if item.book)
    
    def get_item_count(self):
        return sum(item.quantity for item in self.items)
    
    def clear(self):
        for item in self.items:
            db.session.delete(item)
        db.session.commit()
    
    def __repr__(self):
        return f'<Cart {self.id}>'


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_subtotal(self):
        return self.quantity * self.book.price if self.book else 0
    
    def __repr__(self):
        return f'<CartItem {self.id}>'
