import boto3
import json
import base64
import os
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

def test_lambda():
    load_dotenv()
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Load and compress image if needed
    with open('SampleImages/IMG_4653.jpg', 'rb') as f:
        image_data = f.read()
    
    # Compress if too large (6MB limit - 1.5MB buffer for JSON overhead)
    max_size = 4.5 * 1024 * 1024  # 5MB
    print(len(image_data))
    if len(image_data) > max_size:
        img = Image.open(BytesIO(image_data))
        quality = 100
        while quality > 10:
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            compressed_data = buffer.getvalue()
            
            if len(compressed_data) <= max_size:
                image_data = compressed_data
                break
            quality -= 5
    
    test_image = base64.b64encode(image_data).decode('utf-8')
    print(len(image_data))
    
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