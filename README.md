# BookBazaar - E-commerce Bookstore Platform

A comprehensive online bookstore platform built with Python, Flask, and SQLite for local development, designed for future AWS deployment.

## Features

### Customer Features
- Browse and search books by title, author, or category
- View book details with pricing and availability
- Shopping cart functionality
- Secure checkout process
- Order history and tracking

### Seller Features
- Add, edit, and delete book listings
- Inventory management
- Order tracking for their books
- Sales dashboard with statistics

### Admin Features
- User management (activate/deactivate users)
- Seller approval workflow
- Category management
- Order oversight and status updates
- Platform analytics

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone/Navigate to the project**
   ```bash
   cd d:\BookBazaar
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Open in browser**
   ```
   http://localhost:5000
   ```

### Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@bookbazaar.com | admin123 |
| Seller | seller@bookbazaar.com | seller123 |

### Add Sample Data
```bash
python seed_data.py
```

## Project Structure

```
BookBazaar/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py             # Configuration
│   ├── models/               # Database models
│   ├── routes/               # Route blueprints
│   ├── templates/            # Jinja2 templates
│   ├── static/               # CSS, JS, images
│   └── utils/                # Helper functions
├── requirements.txt
├── run.py                    # Entry point
├── seed_data.py              # Sample data script
└── README.md
```

## Tech Stack

- **Backend**: Flask 3.0, Flask-SQLAlchemy, Flask-Login
- **Database**: SQLite (dev), MySQL/DynamoDB (production)
- **Frontend**: Jinja2 templates, CSS3, Font Awesome icons
- **Authentication**: Flask-Login with password hashing

## AWS Deployment

See `AWS_DEPLOYMENT.md` for detailed deployment instructions using:
- Amazon EC2 (hosting)
- Amazon DynamoDB (database)
- AWS SNS (notifications)
- AWS IAM (access control)

## License

This project is for educational purposes.
