import json
import boto3
import base64
from io import StringIO
import csv

def lambda_handler(event, context):
    # Initialize AWS clients
    textract = boto3.client('textract', region_name='us-east-1')
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Get image from API request
    image_data = base64.b64decode(event['body']['image'])
    
    # Extract layout with Textract
    response = textract.analyze_document(
        Document={'Bytes': image_data},
        FeatureTypes=['LAYOUT']
    )
    
    # Convert to CSV
    csv_data = convert_to_csv(response['Blocks'])
    
    # Send to Claude Haiku
    prompt = f"Analyze this layout data:\n{csv_data}"
    
    system_prompt = '''You are a acting as a text processor that extracts the relavant dates from emails and other sources and returns them in a consistent format. No response should be generated other than the formatted data.

The format should be in typical javascript object format:
[
{
startDate: <EST start date of event>,
endDate: <EST time end date of event>,
eventTitle: <event title>,
eventDescription: <event description>
tags: <list of relevant tags, "productivity", "recreaction", "personal", "athletics", ect>
}
]

The current year is 2025'''
    
    bedrock_response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )
    
    result = json.loads(bedrock_response['body'].read())
    
    return {
        'statusCode': 200,
        'body': result['content'][0]['text']
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