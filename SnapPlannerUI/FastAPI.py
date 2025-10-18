from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime
import os
from typing import List
import json
from dotenv import load_dotenv
from image_processor import extract_text_from_image, extract_events_from_text

# Load environment variables from .env file
load_dotenv()

# Access environment variables
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')  # Default to us-east-1 if not specifiedpi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime
import os
from typing import List
import json
from image_processor import extract_text_from_image, extract_events_from_text

# Create directories if they don't exist
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

for directory in [STATIC_DIR, UPLOAD_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Initialize events storage
EVENTS_FILE = "events.json"
def load_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_events(events):
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f)

app = FastAPI()

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/index.html")

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create a unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        try:
            # Save the uploaded file
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Process the image
            text = extract_text_from_image(file_path)
            if not text:
                raise Exception("No text could be extracted from the image")
                
            events = extract_events_from_text(text)
            
            # Save the events
            try:
                current_events = load_events()
                current_events.extend(events)
                save_events(current_events)
            except Exception as e:
                print(f"Error saving events: {str(e)}")
                # Create empty events file if it doesn't exist
                if not os.path.exists(EVENTS_FILE):
                    save_events(events)
                else:
                    raise
            
            return JSONResponse(content={
                "filename": file.filename,
                "status": "File processed successfully",
                "events_found": len(events),
                "events": events
            })
            
        finally:
            # Clean up the uploaded file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing temporary file: {str(e)}")
                    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/events/")
async def get_events():
    events = load_events()
    return events

@app.post("/events/")
async def create_event(event: dict):
    try:
        events = load_events()
        events.append(event)
        save_events(events)
        return {"status": "success", "event": event}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("FastAPI:app", host="0.0.0.0", port=8000, reload=True)
