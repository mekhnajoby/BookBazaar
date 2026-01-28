import boto3
from flask import current_app
from botocore.exceptions import ClientError

def get_boto3_session():
    """Create a boto3 session with configured credentials"""
    return boto3.Session(
        aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
        region_name=current_app.config.get('AWS_REGION')
    )

def get_dynamodb_resource():
    """Get DynamoDB resource"""
    session = get_boto3_session()
    return session.resource('dynamodb')

def get_sns_client():
    """Get SNS client"""
    session = get_boto3_session()
    return session.client('sns')

def send_sns_notification(subject, message):
    """Send SNS notification (replicated from app_aws.py)"""
    if not current_app.config.get('USE_AWS') or not current_app.config.get('SNS_TOPIC_ARN'):
        return False
        
    try:
        sns = get_sns_client()
        sns.publish(
            TopicArn=current_app.config.get('SNS_TOPIC_ARN'),
            Subject=subject,
            Message=message
        )
        return True
    except ClientError as e:
        print(f"Error sending SNS notification: {e}")
        return False
