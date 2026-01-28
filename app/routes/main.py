from flask import Blueprint, render_template, request
from app.models import Book, Category
from sqlalchemy import or_
from app.utils.dynamo_repo import BookRepository, CategoryRepository
from flask import current_app

main_bp = Blueprint('main', __name__)


class MockPagination:
    """Mock pagination for DynamoDB items"""
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1
        self.next_num = page + 1

    def iter_pages(self):
        # Simple version of iter_pages
        return range(1, self.pages + 1)


@main_bp.route('/')
def index():
    """Landing page"""
    if current_app.config.get('USE_AWS'):
        books_repo = BookRepository()
        cat_repo = CategoryRepository()
        all_books = books_repo.get_all()
        # Sort by created_at desc manually
        featured_books = sorted([b for b in all_books if b.get('is_active', True)], 
                                key=lambda x: x.get('created_at', ''), reverse=True)[:8]
        categories = cat_repo.get_all()
    else:
        featured_books = Book.query.filter_by(is_active=True).order_by(Book.created_at.desc()).limit(8).all()
        categories = Category.query.all()
    return render_template('main/index.html', featured_books=featured_books, categories=categories)


@main_bp.route('/books')
def books():
    """Book catalog page"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    category_id = request.args.get('category', type=int)
    sort_by = request.args.get('sort', 'newest')
    
    if current_app.config.get('USE_AWS'):
        books_repo = BookRepository()
        cat_repo = CategoryRepository()
        all_books = [b for b in books_repo.get_all() if b.get('is_active', True)]
        
        if category_id:
            all_books = [b for b in all_books if b.get('category_id') == str(category_id)]
        
        # Sort
        if sort_by == 'price_low':
            all_books.sort(key=lambda x: float(x.get('price', 0)))
        elif sort_by == 'price_high':
            all_books.sort(key=lambda x: float(x.get('price', 0)), reverse=True)
        elif sort_by == 'title':
            all_books.sort(key=lambda x: x.get('title', '').lower())
        else:
            all_books.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
        total = len(all_books)
        start = (page - 1) * per_page
        end = start + per_page
        items = all_books[start:end]
        
        books = MockPagination(items, page, per_page, total)
        categories = cat_repo.get_all()
    else:
        query = Book.query.filter_by(is_active=True)
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if sort_by == 'price_low':
            query = query.order_by(Book.price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Book.price.desc())
        elif sort_by == 'title':
            query = query.order_by(Book.title.asc())
        else:
            query = query.order_by(Book.created_at.desc())
            
        books = query.paginate(page=page, per_page=per_page, error_out=False)
        categories = Category.query.all()
    
    return render_template('main/books.html', 
                          books=books, 
                          categories=categories, 
                          current_category=category_id,
                          sort_by=sort_by)


@main_bp.route('/books/<int:book_id>')
@main_bp.route('/books/<book_id>')
def book_detail(book_id):
    """Book detail page"""
    if current_app.config.get('USE_AWS'):
        book = BookRepository().get_by_id(book_id)
        if not book:
            from flask import abort
            abort(404)
        all_books = BookRepository().get_all()
        related_books = [b for b in all_books if b.get('category_id') == book.get('category_id') and b.get('id') != str(book_id) and b.get('is_active', True)][:4]
    else:
        book = Book.query.get_or_404(book_id)
        related_books = Book.query.filter(
            Book.category_id == book.category_id,
            Book.id != book.id,
            Book.is_active == True
        ).limit(4).all()
    return render_template('main/book_detail.html', book=book, related_books=related_books)


@main_bp.route('/search')
def search():
    """Search books"""
    query_text = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    if current_app.config.get('USE_AWS'):
        books_repo = BookRepository()
        all_books = [b for b in books_repo.get_all() if b.get('is_active', True)]
        
        if query_text:
            q = query_text.lower()
            all_books = [b for b in all_books if 
                         q in b.get('title', '').lower() or 
                         q in b.get('author', '').lower() or 
                         q in b.get('description', '').lower() or 
                         q in b.get('genre', '').lower()]
            
        total = len(all_books)
        start = (page - 1) * per_page
        end = start + per_page
        items = all_books[start:end]
        books = MockPagination(items, page, per_page, total)
    else:
        if query_text:
            books = Book.query.filter(
                Book.is_active == True,
                or_(
                    Book.title.ilike(f'%{query_text}%'),
                    Book.author.ilike(f'%{query_text}%'),
                    Book.description.ilike(f'%{query_text}%'),
                    Book.genre.ilike(f'%{query_text}%')
                )
            ).paginate(page=page, per_page=per_page, error_out=False)
        else:
            books = Book.query.filter_by(is_active=True).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('main/search.html', books=books, query=query_text)


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')


@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('main/contact.html')
