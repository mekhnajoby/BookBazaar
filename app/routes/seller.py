from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Book, Category, Order, OrderItem
from app.utils.decorators import seller_required
from datetime import datetime
from flask import current_app
from app.utils.dynamo_repo import BookRepository, CategoryRepository

seller_bp = Blueprint('seller', __name__)


@seller_bp.route('/dashboard')
@login_required
@seller_required
def dashboard():
    """Seller dashboard with statistics"""
    if current_app.config.get('USE_AWS'):
        books_repo = BookRepository()
        seller_books = [b for b in books_repo.get_all() if b.get('seller_id') == str(current_user.id)]
        total_books = len(seller_books)
        total_stock = sum(int(book.get('stock_quantity', 0)) for book in seller_books)
        
        # In this simplified AWS replication, we might not have full OrderItem mapping for sellers yet
        # but we can mock or scan orders.
        total_sales = 0
        total_orders = 0
        recent_order_items = [] # Simplified for now
    else:
        # Get seller's books
        books = Book.query.filter_by(seller_id=current_user.id).all()
        total_books = len(books)
        total_stock = sum(book.stock_quantity for book in books)
        
        # Get orders containing seller's books
        seller_book_ids = [book.id for book in books]
        order_items = OrderItem.query.filter(OrderItem.book_id.in_(seller_book_ids)).all()
        
        total_sales = sum(item.get_subtotal() for item in order_items)
        total_orders = len(set(item.order_id for item in order_items))
        
        # Recent orders
        recent_order_items = OrderItem.query.filter(
            OrderItem.book_id.in_(seller_book_ids)
        ).order_by(OrderItem.id.desc()).limit(10).all()
    
    return render_template('seller/dashboard.html',
                          total_books=total_books,
                          total_stock=total_stock,
                          total_sales=total_sales,
                          total_orders=total_orders,
                          recent_order_items=recent_order_items)


@seller_bp.route('/books')
@login_required
@seller_required
def books():
    """List seller's books"""
    page = request.args.get('page', 1, type=int)
    
    if current_app.config.get('USE_AWS'):
        books_repo = BookRepository()
        seller_books = [b for b in books_repo.get_all() if b.get('seller_id') == str(current_user.id)]
        seller_books.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        total = len(seller_books)
        per_page = 10
        start = (page - 1) * per_page
        end = start + per_page
        items = seller_books[start:end]
        
        from app.routes.main import MockPagination
        books_paginated = MockPagination(items, page, per_page, total)
        return render_template('seller/books.html', books=books_paginated)
    else:
        books_paginated = Book.query.filter_by(seller_id=current_user.id).order_by(Book.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
        return render_template('seller/books.html', books=books_paginated)


@seller_bp.route('/books/add', methods=['GET', 'POST'])
@login_required
@seller_required
def add_book():
    """Add a new book"""
    categories = Category.query.all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        genre = request.form.get('genre', '').strip()
        publisher = request.form.get('publisher', '').strip()
        publication_date_str = request.form.get('publication_date', '')
        isbn = request.form.get('isbn', '').strip()
        price = request.form.get('price', 0, type=float)
        stock_quantity = request.form.get('stock_quantity', 0, type=int)
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        category_id = request.form.get('category_id', type=int)
        
        errors = []
        
        if not title:
            errors.append('Title is required.')
        if not author:
            errors.append('Author is required.')
        if price <= 0:
            errors.append('Price must be greater than 0.')
        if stock_quantity < 0:
            errors.append('Stock quantity cannot be negative.')
        
        # Check ISBN uniqueness
        if isbn:
            existing = Book.query.filter_by(isbn=isbn).first()
            if existing:
                errors.append('ISBN already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('seller/add_book.html', categories=categories)
        
        # Parse publication date
        publication_date = None
        if publication_date_str:
            try:
                publication_date = datetime.strptime(publication_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if current_app.config.get('USE_AWS'):
            book_data = {
                'title': title,
                'author': author,
                'genre': genre,
                'publisher': publisher,
                'publication_date': publication_date_str,
                'isbn': isbn if isbn else None,
                'price': str(price),
                'stock_quantity': stock_quantity,
                'description': description,
                'image_url': image_url if image_url else None,
                'category_id': str(category_id) if category_id else None,
                'seller_id': str(current_user.id),
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            BookRepository().save(book_data)
        else:
            book = Book(
                title=title,
                author=author,
                genre=genre,
                publisher=publisher,
                publication_date=publication_date,
                isbn=isbn if isbn else None,
                price=price,
                stock_quantity=stock_quantity,
                description=description,
                image_url=image_url if image_url else None,
                category_id=category_id,
                seller_id=current_user.id
            )
            db.session.add(book)
            db.session.commit()
        
        flash(f'Book "{title}" added successfully!', 'success')
        return redirect(url_for('seller.books'))
    
    return render_template('seller/add_book.html', categories=categories)


@seller_bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
@seller_required
def edit_book(book_id):
    """Edit a book"""
    book = Book.query.get_or_404(book_id)
    
    if book.seller_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('seller.books'))
    
    categories = Category.query.all()
    
    if request.method == 'POST':
        book.title = request.form.get('title', '').strip()
        book.author = request.form.get('author', '').strip()
        book.genre = request.form.get('genre', '').strip()
        book.publisher = request.form.get('publisher', '').strip()
        publication_date_str = request.form.get('publication_date', '')
        book.isbn = request.form.get('isbn', '').strip() or None
        book.price = request.form.get('price', 0, type=float)
        book.stock_quantity = request.form.get('stock_quantity', 0, type=int)
        book.description = request.form.get('description', '').strip()
        book.image_url = request.form.get('image_url', '').strip() or None
        book.category_id = request.form.get('category_id', type=int)
        book.is_active = request.form.get('is_active') == 'on'
        
        # Parse publication date
        if publication_date_str:
            try:
                book.publication_date = datetime.strptime(publication_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        db.session.commit()
        flash(f'Book "{book.title}" updated successfully!', 'success')
        return redirect(url_for('seller.books'))
    
    return render_template('seller/edit_book.html', book=book, categories=categories)


@seller_bp.route('/books/delete/<int:book_id>', methods=['POST'])
@login_required
@seller_required
def delete_book(book_id):
    """Delete a book"""
    book = Book.query.get_or_404(book_id)
    
    if book.seller_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('seller.books'))
    
    # Check if book has orders
    if book.order_items.count() > 0:
        # Soft delete - just deactivate
        book.is_active = False
        db.session.commit()
        flash(f'Book "{book.title}" has been deactivated (has existing orders).', 'info')
    else:
        # Hard delete
        title = book.title
        db.session.delete(book)
        db.session.commit()
        flash(f'Book "{title}" deleted successfully!', 'success')
    
    return redirect(url_for('seller.books'))


@seller_bp.route('/orders')
@login_required
@seller_required
def orders():
    """View orders for seller's books"""
    page = request.args.get('page', 1, type=int)
    
    # Get seller's book IDs
    seller_book_ids = [book.id for book in current_user.books]
    
    # Get unique order IDs that contain seller's books
    order_items = OrderItem.query.filter(OrderItem.book_id.in_(seller_book_ids)).all()
    order_ids = list(set(item.order_id for item in order_items))
    
    orders = Order.query.filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('seller/orders.html', orders=orders, seller_book_ids=seller_book_ids)


@seller_bp.route('/inventory')
@login_required
@seller_required
def inventory():
    """Inventory management"""
    books = Book.query.filter_by(seller_id=current_user.id).order_by(Book.stock_quantity.asc()).all()
    low_stock = [book for book in books if book.stock_quantity < 5]
    return render_template('seller/inventory.html', books=books, low_stock=low_stock)


@seller_bp.route('/inventory/update/<int:book_id>', methods=['POST'])
@login_required
@seller_required
def update_stock(book_id):
    """Update book stock"""
    book = Book.query.get_or_404(book_id)
    
    if book.seller_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('seller.inventory'))
    
    stock_quantity = request.form.get('stock_quantity', 0, type=int)
    if stock_quantity >= 0:
        book.stock_quantity = stock_quantity
        db.session.commit()
        flash(f'Stock updated for "{book.title}".', 'success')
    else:
        flash('Stock quantity cannot be negative.', 'danger')
    
    return redirect(url_for('seller.inventory'))
