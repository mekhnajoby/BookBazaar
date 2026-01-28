import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    region = os.environ.get('AWS_REGION', 'us-east-1')
    print(f"Initializing DynamoDB tables in region: {region}")
    
    dynamodb = boto3.resource('dynamodb', region_name=region)
    
    tables = [
        {
            'TableName': os.environ.get('DYNAMODB_USERS_TABLE', 'Users'),
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'id', 'AttributeType': 'S'}]
        },
        {
            'TableName': os.environ.get('DYNAMODB_BOOKS_TABLE', 'Books'),
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'id', 'AttributeType': 'S'}]
        },
        {
            'TableName': os.environ.get('DYNAMODB_CATEGORIES_TABLE', 'Categories'),
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'id', 'AttributeType': 'S'}]
        },
        {
            'TableName': os.environ.get('DYNAMODB_ORDERS_TABLE', 'Orders'),
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'id', 'AttributeType': 'S'}]
        },
        {
            'TableName': os.environ.get('DYNAMODB_CARTS_TABLE', 'Carts'),
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'id', 'AttributeType': 'S'}]
        }
    ]
    
    for table_config in tables:
        try:
            print(f"Creating table {table_config['TableName']}...")
            table = dynamodb.create_table(
                TableName=table_config['TableName'],
                KeySchema=table_config['KeySchema'],
                AttributeDefinitions=table_config['AttributeDefinitions'],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            print(f"Table {table_config['TableName']} created successfully.")
        except Exception as e:
            if 'ResourceInUseException' in str(e):
                print(f"Table {table_config['TableName']} already exists.")
            else:
                print(f"Error creating table {table_config['TableName']}: {e}")

if __name__ == '__main__':
    create_tables()
