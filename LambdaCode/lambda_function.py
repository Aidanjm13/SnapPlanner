import json
import boto3
import base64
from io import StringIO, BytesIO
import csv
from datetime import datetime, timezone, timedelta
import PyPDF2

def lambda_handler(event, context):
    # Initialize AWS clients
    textract = boto3.client('textract', region_name='us-east-1')
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    

    body = event['body']
    if 'image' in body:
        type = 'image'
    if 'pdf' in body:
        type = 'pdf'
        
    # Get image from API request
    req_data = base64.b64decode(body[type])
    
    # Extract text based on file type
    if type == 'pdf':
        # For PDFs, extract raw text using PyPDF2
        pdf_reader = PyPDF2.PdfReader(BytesIO(req_data))
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        csv_data = text_content
    else:
        # For images, use analyze_document with layout
        response = textract.analyze_document(
            Document={'Bytes': req_data},
            FeatureTypes=['LAYOUT']
        )
        # Convert to CSV
        csv_data = convert_to_csv(response['Blocks'])
    
    # Send to Claude Haiku
    prompt = f"{csv_data}"
    
    est = timezone(timedelta(hours=-5))
    current_date = datetime.now(est).strftime('%Y-%m-%dT%H:%M:%S%z')
    debugLog = current_date
    system_prompt = f'''You are a acting as a text processor that extracts the relavant dates from emails and other sources and returns them in a consistent format. No response should be provided other than the formatted data.

The format should be in typical json object format:
[
{{
"startDate": "<EST start date of event %Y-%m-%dT%H:%M:%S%z>",
"endDate": "<EST time end date of event %Y-%m-%dT%H:%M:%S%z>",
"eventTitle": "<title of event>",
"eventDescription": "<short event description>",
"tags": "<list of relevant tags, "productivity", "recreation", "personal", "athletics", ect>"
}}
]

The current date is {current_date}
Make sure to find ALL events and important deadlines.
'''
    
    bedrock_response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 2500,
            'temperature': 0.5,
            'system': system_prompt,
            # 'tools': [{
            #     'name': 'extract_events',
            #     'description': 'Extract events from document text',
            #     'input_schema': {
            #         'type': 'object',
            #         'properties': {
            #             'events': {
            #                 'type': 'array',
            #                 'items': {
            #                     'type': 'object',
            #                     'properties': {
            #                         'startDate': {'type': 'string', 'description': 'ISO format with EST timezone'},
            #                         'endDate': {'type': 'string', 'description': 'ISO format with EST timezone'},
            #                         'eventTitle': {'type': 'string'},
            #                         'eventDescription': {'type': 'string'},
            #                         'tags': {'type': 'array', 'items': {'type': 'string'}}
            #                     },
            #                     'required': ['startDate', 'endDate', 'eventTitle', 'eventDescription', 'tags']
            #                 }
            #             }
            #         },
            #         'required': ['events']
            #     }
            # }],
            # 'tool_choice': {'type': 'tool', 'name': 'extract_events'},
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )
    
    result = json.loads(bedrock_response['body'].read())
    
    return {
        'statusCode': 200,
        'body': result['content'][0]['text'],
        'debug': debugLog
    }

def convert_to_csv(blocks):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Type', 'Text', 'Confidence', 'Left', 'Top', 'Width', 'Height'])
    
    for block in blocks:
        if block['BlockType'] in ['LINE', 'WORD']:
            bbox = block.get('Geometry', {}).get('BoundingBox', {})
            writer.writerow([
                block['BlockType'],
                block.get('Text', ''),
                block.get('Confidence', 0),
                bbox.get('Left', 0),
                bbox.get('Top', 0),
                bbox.get('Width', 0),
                bbox.get('Height', 0)
            ])
    
    return output.getvalue()