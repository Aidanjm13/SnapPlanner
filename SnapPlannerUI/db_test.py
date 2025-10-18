import boto3
from botocore.config import Config

# Create DynamoDB client with temporary credentials
dynamodb = boto3.client('dynamodb',
    region_name='us-east-1',
    config=Config(
        retries = dict(
            max_attempts = 2
        )
    )
)

# Try to create a table
try:
    table = dynamodb.create_table(
        TableName='SnapPlannerEvents',
        KeySchema=[
            {
                'AttributeName': 'user_id',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'event_id',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'user_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'event_id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    print("Table created successfully!")
except Exception as e:
    print(f"Error creating table: {str(e)}")

# List existing tables
try:
    response = dynamodb.list_tables()
    print("\nExisting tables:")
    print(response['TableNames'])
except Exception as e:
    print(f"Error listing tables: {str(e)}")