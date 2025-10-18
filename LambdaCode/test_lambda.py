import boto3
import json
import base64
import os
from dotenv import load_dotenv

def test_lambda():
    load_dotenv()
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Load actual JPG from SampleImages
    with open('SampleImages/IMG_4652.jpg', 'rb') as f:
        test_image = base64.b64encode(f.read()).decode('utf-8')
    
    # Test payload
    test_event = {
        'body': {
            'image': test_image
        }
    }
    
    # Invoke Lambda
    response = lambda_client.invoke(
        FunctionName='SnapPlannerFunction',
        Payload=json.dumps(test_event)
    )
    
    result = json.loads(response['Payload'].read())
    print("Lambda Response:", result)
    
    return result

if __name__ == "__main__":
    test_lambda()