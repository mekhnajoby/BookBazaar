from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import boto3
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

# AWS Configuration 
REGION = os.environ.get('AWS_REGION', 'us-east-1')
dynamodb = boto3.resource('dynamodb', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

# Tables
users_table = dynamodb.Table(os.environ.get('DYNAMODB_USERS_TABLE', 'Users'))
books_table = dynamodb.Table(os.environ.get('DYNAMODB_BOOKS_TABLE', 'Books'))
orders_table = dynamodb.Table(os.environ.get('DYNAMODB_ORDERS_TABLE', 'Orders'))
categories_table = dynamodb.Table(os.environ.get('DYNAMODB_CATEGORIES_TABLE', 'Categories'))

def send_notification(subject, message):
    if not SNS_TOPIC_ARN: return
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
    except ClientError as e:
        print(f"Error sending notification: {e}")

@app.route('/')
def index():
    res_books = books_table.scan()
    books = [b for b in res_books.get('Items', []) if b.get('is_active', True)][:8]
    categories = categories_table.scan().get('Items', [])
    return render_template('main/index.html', featured_books=books, categories=categories)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form.get('role', 'customer')
        
        user_id = str(uuid.uuid4())
        user_data = {
            'id': user_id,
            'username': username,
            'email': email,
            'password': password,
            'role': role,
            'is_active': True,
            'is_approved': (role == 'customer'),
            'created_at': datetime.utcnow().isoformat()
        }
        users_table.put_item(Item=user_data)
        send_notification("New User Signup", f"User {username} ({role}) has signed up.")
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        response = users_table.scan(FilterExpression=Attr('email').eq(email))
        items = response.get('Items', [])
        
        if items and check_password_hash(items[0]['password'], password):
            session['user_id'] = items[0]['id']
            session['username'] = items[0]['username']
            session['role'] = items[0].get('role', 'customer')
            send_notification("User Login", f"User {items[0]['username']} has logged in.")
            return redirect(url_for('index'))
        flash("Invalid credentials!", "danger")
    return render_template('auth/login.html')

@app.route('/books')
def books_list():
    res = books_table.scan()
    books = [b for b in res.get('Items', []) if b.get('is_active', True)]
    categories = categories_table.scan().get('Items', [])
    return render_template('main/books.html', books=books, categories=categories)

@app.route('/books/<book_id>')
def book_detail(book_id):
    res = books_table.get_item(Key={'id': book_id})
    book = res.get('Item')
    if not book: return "NotFound", 404
    return render_template('main/book_detail.html', book=book)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
