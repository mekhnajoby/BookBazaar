from flask_mail import Message
from app import mail
from flask import current_app
import logging
from .aws_services import send_sns_notification


def send_email(to, subject, body, html=None):
    """Send email notification"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            body=body,
            html=html
        )
        mail.send(msg)
        return True
    except Exception as e:
        # In development or if using AWS SNS, try SNS as fallback or primary
        if current_app.config.get('USE_AWS'):
            sns_sent = send_sns_notification(subject, f"To: {to}\n\n{body}")
            if sns_sent:
                return True
                
        # In development, just log the email
        logging.info(f"Email would be sent to {to}: {subject}")
        logging.info(f"Body: {body}")
        return False


def send_order_confirmation(order):
    """Send order confirmation email"""
    subject = f"Order Confirmation - {order.order_number}"
    body = f"""
Dear {order.customer.username},

Thank you for your order!

Order Number: {order.order_number}
Order Date: {order.order_date.strftime('%Y-%m-%d %H:%M')}
Total Amount: ${order.total_price:.2f}

Order Items:
"""
    for item in order.items:
        body += f"  - {item.book.title} x {item.quantity} = ${item.get_subtotal():.2f}\n"
    
    body += f"""
Shipping Address: {order.shipping_address}

We will notify you when your order ships.

Thank you for shopping with BookBazaar!
"""
    
    send_email(order.customer.email, subject, body)
    print(f"[EMAIL] Order confirmation sent for {order.order_number}")


def send_order_status_update(order):
    """Send order status update email"""
    subject = f"Order Status Update - {order.order_number}"
    body = f"""
Dear {order.customer.username},

Your order status has been updated.

Order Number: {order.order_number}
New Status: {order.status.upper()}

Thank you for shopping with BookBazaar!
"""
    
    send_email(order.customer.email, subject, body)
    print(f"[EMAIL] Order status update sent for {order.order_number}")


def send_seller_approval_notification(user, approved=True):
    """Send seller approval/rejection notification"""
    if approved:
        subject = "Seller Account Approved - BookBazaar"
        body = f"""
Dear {user.username},

Congratulations! Your seller account has been approved.

You can now start listing your books on BookBazaar.

Login to your seller dashboard to get started.

Welcome to BookBazaar!
"""
    else:
        subject = "Seller Account Application - BookBazaar"
        body = f"""
Dear {user.username},

Thank you for your interest in becoming a seller on BookBazaar.

Unfortunately, we are unable to approve your seller account at this time.

If you have any questions, please contact our support team.

Thank you,
BookBazaar Team
"""
    
    send_email(user.email, subject, body)
    print(f"[EMAIL] Seller {'approval' if approved else 'rejection'} sent to {user.email}")


def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = "Welcome to BookBazaar!"
    body = f"""
Dear {user.username},

Welcome to BookBazaar - your online destination for books!

Your account has been successfully created.

{'Your seller account is pending approval. We will notify you once approved.' if user.role == 'seller' else 'Start browsing our collection and find your next great read!'}

Happy Reading!
BookBazaar Team
"""
    
    send_email(user.email, subject, body)
    print(f"[EMAIL] Welcome email sent to {user.email}")
