from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Book, Cart, CartItem, Order, OrderItem
from app.utils.decorators import customer_required
from app.utils.email import send_order_confirmation
from flask import current_app
from app.utils.dynamo_repo import BookRepository, OrderRepository, CartRepository

customer_bp = Blueprint('customer', __name__)


@customer_bp.route('/dashboard')
@login_required
def dashboard():
    """Customer dashboard"""
    if current_app.config.get('USE_AWS'):
        orders_repo = OrderRepository()
        cart_repo = CartRepository()
        
        all_orders = orders_repo.get_all()
        recent_orders = sorted([o for o in all_orders if o.get('user_id') == str(current_user.id)], 
                               key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        cart_data = cart_repo.get_by_user(current_user.id)
        cart_count = sum(item.get('quantity', 0) for item in cart_data.get('items', [])) if cart_data else 0
    else:
        recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
        cart_count = 0
        if current_user.cart:
            cart_count = current_user.cart.get_item_count()
    
    return render_template('customer/dashboard.html', recent_orders=recent_orders, cart_count=cart_count)


@customer_bp.route('/cart')
@login_required
def cart():
    """View shopping cart"""
    if current_app.config.get('USE_AWS'):
        cart_repo = CartRepository()
        books_repo = BookRepository()
        cart_data = cart_repo.get_by_user(current_user.id)
        if not cart_data:
            cart_data = cart_repo.save({'id': str(current_user.id), 'items': []})
        
        cart_items = []
        total = 0
        for item in cart_data.get('items', []):
            book = books_repo.get_by_id(item['book_id'])
            if book:
                subtotal = float(book.get('price', 0)) * item['quantity']
                cart_items.append({
                    'id': item['book_id'], # Using book_id as item_id for AWS mode
                    'book': book,
                    'quantity': item['quantity'],
                    'get_subtotal': lambda s=subtotal: s
                })
                total += subtotal
    else:
        if not current_user.cart:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()
        
        cart_items = current_user.cart.items.all() if current_user.cart else []
        total = current_user.cart.get_total() if current_user.cart else 0
        
    return render_template('customer/cart.html', cart_items=cart_items, total=total)


@customer_bp.route('/cart/add/<int:book_id>', methods=['POST'])
@customer_bp.route('/cart/add/<book_id>', methods=['POST'])
@login_required
def add_to_cart(book_id):
    """Add book to cart"""
    if current_app.config.get('USE_AWS'):
        books_repo = BookRepository()
        cart_repo = CartRepository()
        book = books_repo.get_by_id(book_id)
        if not book:
            from flask import abort
            abort(404)
            
        if int(book.get('stock_quantity', 0)) <= 0:
            flash('Sorry, this book is out of stock.', 'warning')
            return redirect(url_for('main.book_detail', book_id=book_id))
            
        quantity = int(request.form.get('quantity', 1))
        cart_data = cart_repo.get_by_user(current_user.id)
        if not cart_data:
            cart_data = {'id': str(current_user.id), 'items': []}
            
        # Check if already in
        found = False
        for item in cart_data['items']:
            if item['book_id'] == str(book_id):
                item['quantity'] += quantity
                found = True
                break
        if not found:
            cart_data['items'].append({'book_id': str(book_id), 'quantity': quantity})
            
        cart_repo.save(cart_data)
        flash(f'"{book.get("title")}" added to cart!', 'success')
        cart_count = sum(i.get('quantity', 0) for i in cart_data['items'])
    else:
        book = Book.query.get_or_404(book_id)
        if not book.is_in_stock():
            flash('Sorry, this book is out of stock.', 'warning')
            return redirect(url_for('main.book_detail', book_id=book_id))
        
        quantity = int(request.form.get('quantity', 1))
        if not current_user.cart:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()
        
        cart_item = CartItem.query.filter_by(cart_id=current_user.cart.id, book_id=book_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(cart_id=current_user.cart.id, book_id=book_id, quantity=quantity)
            db.session.add(cart_item)
        db.session.commit()
        flash(f'"{book.title}" added to cart!', 'success')
        cart_count = current_user.cart.get_item_count()
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': cart_count})
    
    return redirect(url_for('customer.cart'))


@customer_bp.route('/cart/update/<int:item_id>', methods=['POST'])
@customer_bp.route('/cart/update/<item_id>', methods=['POST'])
@login_required
def update_cart_item(item_id):
    """Update cart item quantity"""
    if current_app.config.get('USE_AWS'):
        cart_repo = CartRepository()
        cart_data = cart_repo.get_by_user(current_user.id)
        if not cart_data:
            return redirect(url_for('customer.cart'))
        
        quantity = int(request.form.get('quantity', 1))
        new_items = []
        for item in cart_data.get('items', []):
            if item['book_id'] == str(item_id):
                if quantity > 0:
                    item['quantity'] = quantity
                    new_items.append(item)
            else:
                new_items.append(item)
        cart_data['items'] = new_items
        cart_repo.save(cart_data)
    else:
        cart_item = CartItem.query.get_or_404(item_id)
        if cart_item.cart.user_id != current_user.id:
            flash('Unauthorized action.', 'danger')
            return redirect(url_for('customer.cart'))
        quantity = int(request.form.get('quantity', 1))
        if quantity <= 0:
            db.session.delete(cart_item)
        else:
            cart_item.quantity = quantity
        db.session.commit()
        
    return redirect(url_for('customer.cart'))


@customer_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@customer_bp.route('/cart/remove/<item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    """Remove item from cart"""
    if current_app.config.get('USE_AWS'):
        cart_repo = CartRepository()
        cart_data = cart_repo.get_by_user(current_user.id)
        if cart_data:
            cart_data['items'] = [i for i in cart_data.get('items', []) if i['book_id'] != str(item_id)]
            cart_repo.save(cart_data)
    else:
        cart_item = CartItem.query.get_or_404(item_id)
        if cart_item.cart.user_id != current_user.id:
            flash('Unauthorized action.', 'danger')
            return redirect(url_for('customer.cart'))
        db.session.delete(cart_item)
        db.session.commit()
    
    flash('Item removed from cart.', 'info')
    return redirect(url_for('customer.cart'))


@customer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout page"""
    if current_app.config.get('USE_AWS'):
        cart_repo = CartRepository()
        books_repo = BookRepository()
        order_repo = OrderRepository()
        
        cart_data = cart_repo.get_by_user(current_user.id)
        if not cart_data or not cart_data.get('items'):
            flash('Your cart is empty.', 'warning')
            return redirect(url_for('main.books'))
            
        cart_items = []
        total = 0
        for item in cart_data['items']:
            book = books_repo.get_by_id(item['book_id'])
            if book:
                cart_items.append({'book': book, 'quantity': item['quantity'], 'price': book.get('price')})
                total += float(book.get('price', 0)) * item['quantity']
                
        if request.method == 'POST':
            shipping_address = request.form.get('shipping_address', '').strip()
            if not shipping_address:
                flash('Please enter a shipping address.', 'danger')
                return render_template('customer/checkout.html', cart_items=cart_items, total=total)
                
            order_data = {
                'id': str(uuid.uuid4()) if 'uuid' in globals() else str(datetime.now().timestamp()), # Placeholder
                'order_number': f"BB-{int(datetime.now().timestamp())}",
                'user_id': str(current_user.id),
                'shipping_address': shipping_address,
                'total_price': str(total),
                'status': 'confirmed',
                'created_at': datetime.utcnow().isoformat(),
                'items': [{'book_id': i['book']['id'], 'quantity': i['quantity'], 'price': str(i['price'])} for i in cart_items]
            }
            order_repo.save(order_data)
            cart_repo.save({'id': str(current_user.id), 'items': []})
            
            flash(f'Order placed successfully! Order number: {order_data["order_number"]}', 'success')
            return redirect(url_for('customer.orders'))
    else:
        if not current_user.cart or current_user.cart.get_item_count() == 0:
            flash('Your cart is empty.', 'warning')
            return redirect(url_for('main.books'))
        
        cart_items = current_user.cart.items.all()
        total = current_user.cart.get_total()
        
        if request.method == 'POST':
            shipping_address = request.form.get('shipping_address', '').strip()
            payment_method = request.form.get('payment_method', 'cod')
            notes = request.form.get('notes', '').strip()
            
            if not shipping_address:
                flash('Please enter a shipping address.', 'danger')
                return render_template('customer/checkout.html', cart_items=cart_items, total=total)
            
            order = Order(
                order_number=Order.generate_order_number(),
                user_id=current_user.id,
                shipping_address=shipping_address,
                payment_method=payment_method,
                notes=notes,
                status='confirmed'
            )
            db.session.add(order)
            for item in cart_items:
                order_item = OrderItem(order=order, book_id=item.book_id, quantity=item.quantity, price=item.book.price)
                db.session.add(order_item)
                item.book.reduce_stock(item.quantity)
            order.calculate_total()
            current_user.cart.clear()
            db.session.commit()
            send_order_confirmation(order)
            flash(f'Order placed successfully! Order number: {order.order_number}', 'success')
            return redirect(url_for('customer.order_detail', order_id=order.id))
            
    return render_template('customer/checkout.html', cart_items=cart_items, total=total)


@customer_bp.route('/orders')
@login_required
def orders():
    """Order history"""
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('customer/orders.html', orders=orders)


@customer_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail page"""
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id and not current_user.is_admin():
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('customer.orders'))
    
    return render_template('customer/order_detail.html', order=order)
