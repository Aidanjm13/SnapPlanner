from dotenv import load_dotenv
import os
import boto3

print("Before loading .env:")
print(f"AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID')}")

load_dotenv()

print("\nAfter loading .env:")
print(f"AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID')}")
print(f"AWS_SECRET_ACCESS_KEY: {os.getenv('AWS_SECRET_ACCESS_KEY')[:10]}...")
print(f"AWS_SESSION_TOKEN: {os.getenv('AWS_SESSION_TOKEN')[:50]}...")

# Test with explicit credentials
try:
    dynamodb = boto3.resource('dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_DEFAULT_REGION')
    )
    
    table = dynamodb.Table('Users')
    response = table.get_item(Key={'username': 'test'})
    print("SUCCESS: AWS connection works")
    
except Exception as e:
    print(f"ERROR: {e}")