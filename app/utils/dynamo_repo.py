from flask import current_app
from .aws_services import get_dynamodb_resource
from boto3.dynamodb.conditions import Key, Attr
import uuid
from datetime import datetime

class DynamoRepository:
    def __init__(self, table_name):
        self.table_name = table_name
        self.resource = None
        self._table = None

    @property
    def table(self):
        if self._table is None:
            self.resource = get_dynamodb_resource()
            self._table = self.resource.Table(self.table_name)
        return self._table

    def get_all(self):
        response = self.table.scan()
        return response.get('Items', [])

    def get_by_id(self, item_id):
        response = self.table.get_item(Key={'id': str(item_id)})
        return response.get('Item')

    def save(self, item_data):
        if 'id' not in item_data:
            item_data['id'] = str(uuid.uuid4())
        if 'created_at' not in item_data:
            item_data['created_at'] = datetime.utcnow().isoformat()
        item_data['updated_at'] = datetime.utcnow().isoformat()
        
        self.table.put_item(Item=item_data)
        return item_data

    def delete(self, item_id):
        self.table.delete_item(Key={'id': str(item_id)})
        return True

class UserRepository(DynamoRepository):
    def __init__(self):
        table_name = current_app.config.get('DYNAMODB_USERS_TABLE', 'Users')
        super().__init__(table_name)

    def get_by_email(self, email):
        response = self.table.scan(FilterExpression=Attr('email').eq(email))
        items = response.get('Items', [])
        return items[0] if items else None

    def get_by_username(self, username):
        response = self.table.scan(FilterExpression=Attr('username').eq(username))
        items = response.get('Items', [])
        return items[0] if items else None

class BookRepository(DynamoRepository):
    def __init__(self):
        table_name = current_app.config.get('DYNAMODB_BOOKS_TABLE', 'Books')
        super().__init__(table_name)

    def get_by_category(self, category_id):
        response = self.table.scan(FilterExpression=Attr('category_id').eq(str(category_id)))
        return response.get('Items', [])

    def get_by_seller(self, seller_id):
        response = self.table.scan(FilterExpression=Attr('seller_id').eq(str(seller_id)))
        return response.get('Items', [])

class OrderRepository(DynamoRepository):
    def __init__(self):
        table_name = current_app.config.get('DYNAMODB_ORDERS_TABLE', 'Orders')
        super().__init__(table_name)

    def get_by_user(self, user_id):
        response = self.table.scan(FilterExpression=Attr('user_id').eq(str(user_id)))
        return response.get('Items', [])

class CategoryRepository(DynamoRepository):
    def __init__(self):
        table_name = current_app.config.get('DYNAMODB_CATEGORIES_TABLE', 'Categories')
        super().__init__(table_name)

class CartRepository(DynamoRepository):
    def __init__(self):
        # We'll use a Cart table or just store cart in Users. 
        # For this project, let's use a separate Carts table for clean replication.
        table_name = current_app.config.get('DYNAMODB_CARTS_TABLE', 'Carts')
        super().__init__(table_name)

    def get_by_user(self, user_id):
        response = self.table.get_item(Key={'id': str(user_id)})
        return response.get('Item')
