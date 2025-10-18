import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

def check_users():
    dynamodb = boto3.resource('dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    table = dynamodb.Table('Users')
    
    try:
        response = table.scan()
        users = response['Items']
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"- {user.get('username', 'No username')}")
    except ClientError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_users()