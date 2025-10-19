from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
import uvicorn
from datetime import datetime, timedelta
import os
from typing import List, Optional
import json
from pydantic import BaseModel
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging
import image_processor
import pdf_processor
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

# Security configurations
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing - using SHA256 for simplicity
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# AWS DynamoDB setup
try:
    dynamodb = boto3.resource('dynamodb',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=AWS_REGION,
        config=Config(retries=dict(max_attempts=2))
    )
except Exception as e:
    logger.error(f"Failed to initialize DynamoDB: {e}")
    raise

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserInDB(User):
    hashed_password: str

class Event(BaseModel):
    id: str
    title: str
    start: str
    end: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

# Create directories
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

for directory in [STATIC_DIR, UPLOAD_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

app = FastAPI(title="SnapPlanner API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for public access
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Authentication functions
def verify_password(plain_password, hashed_password):
    return get_password_hash(plain_password) == hashed_password

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    try:
        table = dynamodb.Table('Users')
        response = table.get_item(Key={'username': token_data.username})
        user = response.get('Item')
        
        if user is None:
            raise credentials_exception
        return user
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

# Routes
@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/login.html")

# Authentication routes
@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        table = dynamodb.Table('Users')
        response = table.get_item(Key={'username': form_data.username})
        user = response.get('Item')
        
        if not user or not verify_password(form_data.password, user['password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user['username']}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise HTTPException(status_code=500, detail="Database tables not set up. Run setup_db.py first.")
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication service error: {e.response['Error']['Code']}")

@app.get("/debug/tables")
async def debug_tables():
    try:
        tables = list(dynamodb.tables.all())
        return {"tables": [table.name for table in tables]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/auth/register")
async def register(user_data: UserCreate):
    try:
        table = dynamodb.Table('Users')
        
        # Check if user exists
        try:
            response = table.get_item(Key={'username': user_data.username})
            if 'Item' in response:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database tables not set up. Run setup_db.py first."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database error: {e.response['Error']['Code']}"
                )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = {
            'username': user_data.username,
            'password': hashed_password,
            'email': user_data.email
        }
        
        table.put_item(Item=user)
        return {"message": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration service error: {str(e)}")

# Event routes
@app.get("/events/", response_model=List[Event])
async def get_user_events(current_user: User = Depends(get_current_user)):
    try:
        table = dynamodb.Table('Events')
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(current_user['username'])
        )
        return response['Items']
    except ClientError as e:
        logger.error(f"Get events error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve events")

@app.post("/events/")
async def create_event(event: Event, current_user: User = Depends(get_current_user)):
    try:
        table = dynamodb.Table('Events')
        event_item = event.dict()
        event_item['user_id'] = current_user['username']
        
        table.put_item(Item=event_item)
        return {"message": "Event created successfully"}
    except ClientError as e:
        logger.error(f"Create event error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create event")

@app.delete("/events/{event_id}")
async def delete_event(event_id: str, current_user: User = Depends(get_current_user)):
    try:
        table = dynamodb.Table('Events')
        table.delete_item(
            Key={
                'user_id': current_user['username'],
                'id': event_id
            }
        )
        return {"message": "Event deleted successfully"}
    except ClientError as e:
        logger.error(f"Delete event error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete event")

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...), token: str = None):
    # Validate token if provided
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    try:
        # Validate file type
        if not (file.content_type.startswith('image/') or file.content_type == 'application/pdf'):
            raise HTTPException(status_code=400, detail="File must be an image or PDF")
        
        # Create unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        try:
            # Save uploaded file
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Process file based on type
            if file.content_type == 'application/pdf':
                events = pdf_processor.pdfToEvents(file_path)['events']
            else:
                events = image_processor.imageToEvents(file_path)['events']

            os.remove(file_path)
            
            return JSONResponse(content={
                "status": "File uploaded successfully",
                "events": events
            })
            
        finally:
            # Clean up
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error removing temporary file: {e}")
                    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="File processing failed")

if __name__ == "__main__":
    uvicorn.run("FastAPI:app", host="0.0.0.0", port=80, reload=False)