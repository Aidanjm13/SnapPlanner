import boto3
from dotenv import load_dotenv
import os

load_dotenv()

print("Testing AWS credentials...")
print(f"Access Key: {os.getenv('AWS_ACCESS_KEY_ID')[:10]}...")
print(f"Region: {os.getenv('AWS_DEFAULT_REGION')}")

try:
    # Test without session token first
    dynamodb = boto3.resource('dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION')
    )
    
    table = dynamodb.Table('Users')
    response = table.get_item(Key={'username': 'test'})
    print("✓ Connection successful without session token")
    
except Exception as e:
    print(f"✗ Error without session token: {e}")
    
    try:
        # Test with session token
        dynamodb = boto3.resource('dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
            region_name=os.getenv('AWS_DEFAULT_REGION')
        )
        
        table = dynamodb.Table('Users')
        response = table.get_item(Key={'username': 'test'})
        print("✓ Connection successful with session token")
        
    except Exception as e2:
        print(f"✗ Error with session token: {e2}")