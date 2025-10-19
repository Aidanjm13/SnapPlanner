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


def imageToEvents(image_path):
    load_dotenv()
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Load and compress image if needed
    with open(image_path, 'rb') as f:
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

    print(response)
    
    result = json.loads(response['Payload'].read())
    print("Lambda result:", result)
    
    # Handle different response structures

    if isinstance(result.get('body'), str):
        events_text = result['body']
    else:
        events_text = json.dumps(result['body'])#['content'][0]['text']
    print(events_text)

    events = json.loads('{"events": ' + events_text + '}')

        
    print("Parsed events:", events)
    return events

    try:
        # If on Windows, you might need to set the tesseract path
        # Uncomment and modify the line below if Tesseract is not in your PATH
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Open and process the image
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise Exception(f"Error processing image with Tesseract OCR: {str(e)}")
    


def parse_date_time(text):
    """Try to parse date and time from text"""
    # Extended date patterns
    date_patterns = [
        # Common date formats
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
        # Additional date formats
        r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',  # ISO format
        r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}\b'
    ]
    
    # Time patterns
    time_patterns = [
        r'\b(?:1[0-2]|0?[1-9])(?::[0-5][0-9])?\s*(?:AM|PM)\b',
        r'\b(?:2[0-3]|[01]?[0-9]):[0-5][0-9]\b'  # 24-hour format
    ]
    
    # Try to find a date
    date_str = None
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group()
            break
    
    # Try to find a time
    time_str = None
    for pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            time_str = match.group()
            break
    
    # Parse the date
    if date_str:
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y",
            "%B %d, %Y", "%b %d, %Y", "%Y/%m/%d",
            "%A, %B %d", "%a, %b %d"
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # If we only have day and month, add current year
                if fmt in ["%A, %B %d", "%a, %b %d"]:
                    parsed_date = parsed_date.replace(year=datetime.now().year)
                return parsed_date, time_str
            except ValueError:
                continue
    
    return None, time_str

def extract_events_from_text(text):
    """Extract potential event information from text using enhanced parsing"""
    events = []
    lines = text.split('\n')
    
    current_date = None
    current_time = None
    current_description = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Try to parse date and time from the line
        parsed_date, parsed_time = parse_date_time(line)
        
        if parsed_date:
            # If we have a previous event, save it
            if current_date and current_description:
                event = {
                    "title": " ".join(current_description).strip(),
                    "start": current_date.strftime("%Y-%m-%d")
                }
                if current_time:
                    event["title"] = f"{current_time} - {event['title']}"
                events.append(event)
            
            # Start new event
            current_date = parsed_date
            current_time = parsed_time
            current_description = []
            
            # Add any remaining text from the current line as description
            remaining_text = line
            if parsed_time:
                remaining_text = re.sub(parsed_time, '', remaining_text, flags=re.IGNORECASE)
            remaining_text = re.sub(r'\b' + re.escape(parsed_date.strftime("%B %d, %Y")) + r'\b', '', remaining_text, flags=re.IGNORECASE)
            if remaining_text.strip():
                current_description.append(remaining_text.strip())
            
        elif current_date:
            # If we find a time in a following line, update the current time
            if not current_time:
                _, new_time = parse_date_time(line)
                if new_time:
                    current_time = new_time
                    line = re.sub(new_time, '', line, flags=re.IGNORECASE)
            
            if line.strip():
                current_description.append(line.strip())
    
    # Don't forget to add the last event
    if current_date and current_description:
        event = {
            "title": " ".join(current_description).strip(),
            "start": current_date.strftime("%Y-%m-%d")
        }
        if current_time:
            event["title"] = f"{current_time} - {event['title']}"
        events.append(event)
    
    return events