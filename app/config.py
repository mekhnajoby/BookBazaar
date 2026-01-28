import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///bookbazaar.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@bookbazaar.com')
    
    # AWS Settings
    USE_AWS = os.environ.get('USE_AWS', 'False').lower() == 'true'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
    
    # DynamoDB Table Names
    DYNAMODB_USERS_TABLE = os.environ.get('DYNAMODB_USERS_TABLE', 'Users')
    DYNAMODB_BOOKS_TABLE = os.environ.get('DYNAMODB_BOOKS_TABLE', 'Books')
    DYNAMODB_ORDERS_TABLE = os.environ.get('DYNAMODB_ORDERS_TABLE', 'Orders')
    DYNAMODB_CATEGORIES_TABLE = os.environ.get('DYNAMODB_CATEGORIES_TABLE', 'Categories')
    DYNAMODB_CARTS_TABLE = os.environ.get('DYNAMODB_CARTS_TABLE', 'Carts')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
