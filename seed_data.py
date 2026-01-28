"""Script to add sample books to the database"""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Book, Category, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Create a sample seller
    seller = User.query.filter_by(email='seller@bookbazaar.com').first()
    if not seller:
        seller = User(
            username='bookstore',
            email='seller@bookbazaar.com',
            password=generate_password_hash('seller123'),
            role='seller',
            is_active=True,
            is_approved=True
        )
        db.session.add(seller)
        db.session.commit()
        print("Created sample seller: seller@bookbazaar.com / seller123")
    
    # Get categories
    categories = {cat.category_name: cat.id for cat in Category.query.all()}
    
    # Sample books
    sample_books = [
        {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "price": 12.99, "stock_quantity": 50, "category": "Fiction", "description": "A classic novel of the Jazz Age."},
        {"title": "To Kill a Mockingbird", "author": "Harper Lee", "price": 14.99, "stock_quantity": 35, "category": "Fiction", "description": "A gripping tale of racial injustice."},
        {"title": "1984", "author": "George Orwell", "price": 11.99, "stock_quantity": 40, "category": "Fiction", "description": "A dystopian social science fiction novel."},
        {"title": "Pride and Prejudice", "author": "Jane Austen", "price": 10.99, "stock_quantity": 30, "category": "Fiction", "description": "A romantic novel of manners."},
        {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "price": 13.99, "stock_quantity": 25, "category": "Fiction", "description": "A story about teenage angst and alienation."},
        {"title": "Sapiens: A Brief History", "author": "Yuval Noah Harari", "price": 18.99, "stock_quantity": 45, "category": "Non-Fiction", "description": "A journey through humanity's history."},
        {"title": "Atomic Habits", "author": "James Clear", "price": 16.99, "stock_quantity": 60, "category": "Self-Help", "description": "Tiny changes, remarkable results."},
        {"title": "The Lean Startup", "author": "Eric Ries", "price": 15.99, "stock_quantity": 30, "category": "Business & Economics", "description": "How to build a successful startup."},
        {"title": "Brief History of Time", "author": "Stephen Hawking", "price": 17.99, "stock_quantity": 25, "category": "Science & Technology", "description": "Exploring the universe's mysteries."},
        {"title": "Harry Potter and the Sorcerer's Stone", "author": "J.K. Rowling", "price": 14.99, "stock_quantity": 100, "category": "Children's Books", "description": "The beginning of the magical journey."},
    ]
    
    for book_data in sample_books:
        existing = Book.query.filter_by(title=book_data["title"]).first()
        if not existing:
            book = Book(
                title=book_data["title"],
                author=book_data["author"],
                price=book_data["price"],
                stock_quantity=book_data["stock_quantity"],
                description=book_data["description"],
                category_id=categories.get(book_data["category"]),
                seller_id=seller.id
            )
            db.session.add(book)
            print(f"Added: {book_data['title']}")
    
    db.session.commit()
    print("\nSample data added successfully!")
    print("\nLogin credentials:")
    print("Admin: admin@bookbazaar.com / admin123")
    print("Seller: seller@bookbazaar.com / seller123")
