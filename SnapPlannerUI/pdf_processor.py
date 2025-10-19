import boto3
import json
import base64
from datetime import datetime, timezone, timedelta
from PIL import Image
import pytesseract
import re
from datetime import datetime
import json
import os
import boto3
import json
import base64
from dotenv import load_dotenv
from io import BytesIO


    
def pdfToEvents(pdf_path):
    load_dotenv()
    lambda_client = boto3.client('lambda', region_name='us-east-1')

    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()
    

    test_pdf = base64.b64encode(pdf_data).decode('utf-8')
    print(len(pdf_data))
    
    # payload
    test_event = {
        'body': {
            'pdf': test_pdf
        }
    }
    
    # Invoke Lambda
    response = lambda_client.invoke(
        FunctionName='SnapPlannerFunction',
        Payload=json.dumps(test_event)
    )


    print(response)
    result = json.loads(response['Payload'].read())
    print(result)

    try:
        events = json.loads('{"events": '+result['body'] + '}')
    except json.JSONDecodeError as e:
        # Handle unterminated string/object from token limit
        response_text = result['body']
        
        # Find the last complete event object
        last_brace = response_text.rfind('}')
        if last_brace != -1:
            # Truncate to last complete object and close array
            truncated = response_text[:last_brace + 1] + ']'
            try:
                events = json.loads('{"events": ' + truncated + '}')
            except:
                events = {"events": []}
        else:
            events = {"events": []}
    
    print(events)
    
    return events