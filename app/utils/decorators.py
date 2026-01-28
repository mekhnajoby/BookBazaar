from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user


def login_required_with_role(*roles):
    """Decorator to require login and specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if roles and current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('Admin access required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def seller_required(f):
    """Decorator to require approved seller role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_seller():
            flash('Seller access required.', 'danger')
            abort(403)
        if not current_user.is_approved:
            flash('Your seller account is pending approval.', 'warning')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def customer_required(f):
    """Decorator to require customer role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role not in ['customer', 'admin']:
            flash('Customer access required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
