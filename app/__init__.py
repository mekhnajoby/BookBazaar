from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///bookbazaar.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 25))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Import models
    from app.models import User, Book, Category, Order, OrderItem, Cart, CartItem
    
    @login_manager.user_loader
    def load_user(user_id):
        if app.config.get('USE_AWS'):
            from app.utils.dynamo_repo import UserRepository
            user_data = UserRepository().get_by_id(user_id)
            if user_data:
                # Reconstruct User object from dict without DB session
                user = User()
                for key, value in user_data.items():
                    setattr(user, key, value)
                return user
            return None
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.customer import customer_bp
    from app.routes.seller import seller_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(seller_bp, url_prefix='/seller')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create tables
    if not app.config.get('USE_AWS'):
        with app.app_context():
            db.create_all()
            # Create default admin if not exists
            create_default_admin()
            # Create default categories
            create_default_categories()
    
    return app


def create_default_admin():
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(email='admin@bookbazaar.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@bookbazaar.com',
            password=generate_password_hash('admin123'),
            role='admin',
            is_active=True,
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()


def create_default_categories():
    from app.models import Category
    
    categories = [
        ('Fiction', 'Novels, short stories, and literary fiction'),
        ('Non-Fiction', 'Biographies, memoirs, and factual books'),
        ('Science & Technology', 'Science, technology, and innovation'),
        ('Business & Economics', 'Business, finance, and economics'),
        ('Self-Help', 'Personal development and self-improvement'),
        ('Children\'s Books', 'Books for children and young readers'),
        ('Academic', 'Textbooks and academic resources'),
        ('Comics & Graphic Novels', 'Comics, manga, and graphic novels')
    ]
    
    for name, description in categories:
        if not Category.query.filter_by(category_name=name).first():
            category = Category(category_name=name, description=description)
            db.session.add(category)
    
    db.session.commit()
