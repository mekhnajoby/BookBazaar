from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='customer')  # customer, seller, admin
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True)  # For seller approval
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy='dynamic', foreign_keys='Order.user_id')
    books = db.relationship('Book', backref='seller', lazy='dynamic', foreign_keys='Book.seller_id')
    cart = db.relationship('Cart', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_seller(self):
        return self.role == 'seller'
    
    def is_customer(self):
        return self.role == 'customer'
    
    def is_approved_seller(self):
        return self.role == 'seller' and self.is_approved
    
    def __repr__(self):
        return f'<User {self.username}>'
