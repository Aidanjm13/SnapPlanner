import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    """Create DynamoDB tables for Users and Events"""
    
    dynamodb = boto3.resource('dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    # Create Users table
    try:
        users_table = dynamodb.create_table(
            TableName='Users',
            KeySchema=[
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'username',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Creating Users table...")
        users_table.wait_until_exists()
        print("Users table created successfully!")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Users table already exists")
        else:
            print(f"Error creating Users table: {e}")
    
    # Create Events table
    try:
        events_table = dynamodb.create_table(
            TableName='Events',
            KeySchema=[
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'id',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Creating Events table...")
        events_table.wait_until_exists()
        print("Events table created successfully!")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Events table already exists")
        else:
            print(f"Error creating Events table: {e}")

if __name__ == "__main__":
    create_tables()