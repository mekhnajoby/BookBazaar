from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Cart
from app.utils.email import send_welcome_email
from app.utils.dynamo_repo import UserRepository
from flask import current_app

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'customer')
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if current_app.config.get('USE_AWS'):
            user_repo = UserRepository()
            if user_repo.get_by_username(username):
                errors.append('Username already exists.')
            if user_repo.get_by_email(email):
                errors.append('Email already registered.')
        else:
            if User.query.filter_by(username=username).first():
                errors.append('Username already exists.')
            
            if User.query.filter_by(email=email).first():
                errors.append('Email already registered.')
        
        if role not in ['customer', 'seller']:
            role = 'customer'
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')
        
        if current_app.config.get('USE_AWS'):
            user_data = {
                'username': username,
                'email': email,
                'password': generate_password_hash(password),
                'role': role,
                'address': address,
                'phone': phone,
                'is_active': True,
                'is_approved': (role == 'customer')
            }
            user_repo = UserRepository()
            user_dict = user_repo.save(user_data)
            
            # Reconstruct user object for login/email helpers
            user = User()
            for key, val in user_dict.items():
                setattr(user, key, val)
        else:
            user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                role=role,
                address=address,
                phone=phone,
                is_active=True,
                is_approved=(role == 'customer')
            )
            db.session.add(user)
            db.session.commit()
            
            if role == 'customer':
                cart = Cart(user_id=user.id)
                db.session.add(cart)
                db.session.commit()
        
        # Send welcome email
        send_welcome_email(user)
        
        if role == 'seller':
            flash('Registration successful! Your seller account is pending approval.', 'success')
        else:
            flash('Registration successful! Please log in.', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if current_app.config.get('USE_AWS'):
            user_data = UserRepository().get_by_email(email)
            if user_data:
                user = User()
                for key, val in user_data.items():
                    setattr(user, key, val)
            else:
                user = None
        else:
            user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Ensure customer has a cart
            if user.role == 'customer' and not user.cart:
                cart = Cart(user_id=user.id)
                db.session.add(cart)
                db.session.commit()
            
            # Redirect based on role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.is_seller():
                if user.is_approved:
                    return redirect(url_for('seller.dashboard'))
                else:
                    flash('Your seller account is pending approval.', 'warning')
                    return redirect(url_for('main.index'))
            else:
                return redirect(url_for('customer.dashboard'))
        
        flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        
        errors = []
        
        # Check if username is taken by another user
        existing = User.query.filter(User.username == username, User.id != current_user.id).first()
        if existing:
            errors.append('Username already taken.')
        
        # Check if email is taken by another user
        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing:
            errors.append('Email already registered.')
        
        # Password change
        if new_password:
            if not current_password:
                errors.append('Please enter your current password.')
            elif not current_user.check_password(current_password):
                errors.append('Current password is incorrect.')
            elif len(new_password) < 6:
                errors.append('New password must be at least 6 characters.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/profile.html')
        
        # Update user
        current_user.username = username
        current_user.email = email
        current_user.address = address
        current_user.phone = phone
        
        if new_password:
            current_user.password = generate_password_hash(new_password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html')
