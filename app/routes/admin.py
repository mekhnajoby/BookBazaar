from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Book, Category, Order
from app.utils.decorators import admin_required
from app.utils.email import send_seller_approval_notification, send_order_status_update
from flask import current_app
from app.utils.dynamo_repo import UserRepository, BookRepository, OrderRepository, CategoryRepository

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with analytics"""
    if current_app.config.get('USE_AWS'):
        user_repo = UserRepository()
        books_repo = BookRepository()
        order_repo = OrderRepository()
        
        all_users = user_repo.get_all()
        total_users = len(all_users)
        total_customers = len([u for u in all_users if u.get('role') == 'customer'])
        total_sellers = len([u for u in all_users if u.get('role') == 'seller'])
        pending_sellers = len([u for u in all_users if u.get('role') == 'seller' and not u.get('is_approved', True)])
        
        total_books = len(books_repo.get_all())
        all_orders = order_repo.get_all()
        total_orders = len(all_orders)
        
        total_revenue = sum(float(o.get('total_price', 0)) for o in all_orders if o.get('status') in ['confirmed', 'shipped', 'delivered'])
        
        recent_orders = sorted(all_orders, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
        recent_users = sorted(all_users, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
    else:
        # Statistics
        total_users = User.query.count()
        total_customers = User.query.filter_by(role='customer').count()
        total_sellers = User.query.filter_by(role='seller').count()
        pending_sellers = User.query.filter_by(role='seller', is_approved=False).count()
        
        total_books = Book.query.count()
        total_orders = Order.query.count()
        
        # Revenue
        total_revenue = db.session.query(db.func.sum(Order.total_price)).filter(
            Order.status.in_(['confirmed', 'shipped', 'delivered'])
        ).scalar() or 0
        
        # Recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
        
        # Recent users
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                          total_users=total_users,
                          total_customers=total_customers,
                          total_sellers=total_sellers,
                          pending_sellers=pending_sellers,
                          total_books=total_books,
                          total_orders=total_orders,
                          total_revenue=total_revenue,
                          recent_orders=recent_orders,
                          recent_users=recent_users)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management"""
    page = request.args.get('page', 1, type=int)
    role = request.args.get('role', '')
    search_query = request.args.get('search', '')
    
    if current_app.config.get('USE_AWS'):
        user_repo = UserRepository()
        all_users = user_repo.get_all()
        
        if role:
            all_users = [u for u in all_users if u.get('role') == role]
        
        if search_query:
            s = search_query.lower()
            all_users = [u for u in all_users if s in u.get('username', '').lower() or s in u.get('email', '').lower()]
            
        all_users.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        total = len(all_users)
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        items = all_users[start:end]
        
        from app.routes.main import MockPagination
        users_paginated = MockPagination(items, page, per_page, total)
    else:
        query = User.query
        if role:
            query = query.filter_by(role=role)
        if search_query:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search_query}%'),
                    User.email.ilike(f'%{search_query}%')
                )
            )
        users_paginated = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', users=users_paginated, current_role=role, search=search_query)


@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@admin_bp.route('/users/toggle/<user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """Activate/deactivate user"""
    if current_app.config.get('USE_AWS'):
        user_repo = UserRepository()
        user = user_repo.get_by_id(user_id)
        if not user:
            from flask import abort
            abort(404)
        
        if str(user['id']) == str(current_user.id):
            flash('You cannot deactivate your own account.', 'danger')
            return redirect(url_for('admin.users'))
        
        user['is_active'] = not user.get('is_active', True)
        user_repo.save(user)
        username = user['username']
        is_active = user['is_active']
    else:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('You cannot deactivate your own account.', 'danger')
            return redirect(url_for('admin.users'))
        user.is_active = not user.is_active
        db.session.commit()
        username = user.username
        is_active = user.is_active
    
    status = 'activated' if is_active else 'deactivated'
    flash(f'User "{username}" has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/sellers/pending')
@login_required
@admin_required
def pending_sellers():
    """Pending seller approvals"""
    if current_app.config.get('USE_AWS'):
        user_repo = UserRepository()
        all_users = user_repo.get_all()
        pending = [u for u in all_users if u.get('role') == 'seller' and not u.get('is_approved', True)]
        sellers = sorted(pending, key=lambda x: x.get('created_at', ''), reverse=True)
    else:
        sellers = User.query.filter_by(role='seller', is_approved=False).order_by(User.created_at.desc()).all()
    return render_template('admin/pending_sellers.html', sellers=sellers)


@admin_bp.route('/sellers/approve/<int:user_id>', methods=['POST'])
@admin_bp.route('/sellers/approve/<user_id>', methods=['POST'])
@login_required
@admin_required
def approve_seller(user_id):
    """Approve seller"""
    if current_app.config.get('USE_AWS'):
        user_repo = UserRepository()
        user_data = user_repo.get_by_id(user_id)
        if not user_data or user_data.get('role') != 'seller':
            flash('User is not a seller.', 'danger')
            return redirect(url_for('admin.pending_sellers'))
        
        user_data['is_approved'] = True
        user_repo.save(user_data)
        
        # reconstruct for email
        user = User()
        for k, v in user_data.items(): setattr(user, k, v)
        username = user_data['username']
    else:
        user = User.query.get_or_404(user_id)
        if user.role != 'seller':
            flash('User is not a seller.', 'danger')
            return redirect(url_for('admin.pending_sellers'))
        user.is_approved = True
        db.session.commit()
        username = user.username
    
    # Send notification
    send_seller_approval_notification(user, approved=True)
    
    flash(f'Seller "{username}" has been approved.', 'success')
    return redirect(url_for('admin.pending_sellers'))


@admin_bp.route('/sellers/reject/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_seller(user_id):
    """Reject seller"""
    user = User.query.get_or_404(user_id)
    
    if user.role != 'seller':
        flash('User is not a seller.', 'danger')
        return redirect(url_for('admin.pending_sellers'))
    
    # Send notification before deletion
    send_seller_approval_notification(user, approved=False)
    
    # Change to customer instead of deleting
    user.role = 'customer'
    user.is_approved = True
    db.session.commit()
    
    flash(f'Seller application for "{user.username}" has been rejected.', 'info')
    return redirect(url_for('admin.pending_sellers'))


@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """Category management"""
    categories = Category.query.order_by(Category.category_name).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    """Add category"""
    name = request.form.get('category_name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('admin.categories'))
    
    if Category.query.filter_by(category_name=name).first():
        flash('Category already exists.', 'danger')
        return redirect(url_for('admin.categories'))
    
    category = Category(category_name=name, description=description)
    db.session.add(category)
    db.session.commit()
    
    flash(f'Category "{name}" added successfully!', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/edit/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def edit_category(category_id):
    """Edit category"""
    category = Category.query.get_or_404(category_id)
    
    name = request.form.get('category_name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('admin.categories'))
    
    # Check for duplicate
    existing = Category.query.filter(Category.category_name == name, Category.id != category_id).first()
    if existing:
        flash('Category name already exists.', 'danger')
        return redirect(url_for('admin.categories'))
    
    category.category_name = name
    category.description = description
    db.session.commit()
    
    flash(f'Category "{name}" updated successfully!', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has books
    if category.books.count() > 0:
        flash(f'Cannot delete category "{category.category_name}" - it has books assigned.', 'danger')
        return redirect(url_for('admin.categories'))
    
    name = category.category_name
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category "{name}" deleted successfully!', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """All orders"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/orders.html', orders=orders, current_status=status)


@admin_bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    """Order detail"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    
    new_status = request.form.get('status', '')
    valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
    
    if new_status not in valid_statuses:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.order_detail', order_id=order_id))
    
    old_status = order.status
    order.status = new_status
    db.session.commit()
    
    # Send notification
    if old_status != new_status:
        send_order_status_update(order)
    
    flash(f'Order status updated to "{new_status}".', 'success')
    return redirect(url_for('admin.order_detail', order_id=order_id))


@admin_bp.route('/books')
@login_required
@admin_required
def books():
    """All books"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    
    query = Book.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    books = query.order_by(Book.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    categories = Category.query.all()
    
    return render_template('admin/books.html', books=books, categories=categories, current_category=category_id)
