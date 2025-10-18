import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

def test_aws_connection():
    try:
        dynamodb = boto3.resource('dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Try to list tables
        tables = list(dynamodb.tables.all())
        print(f"Connection successful! Found {len(tables)} tables")
        for table in tables:
            print(f"- {table.name}")
            
    except ClientError as e:
        print(f"AWS Connection failed: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_aws_connection()