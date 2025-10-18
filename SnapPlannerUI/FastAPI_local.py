from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
import uvicorn
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from typing import List, Optional
from pydantic import BaseModel

# Security configurations
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Local storage files
USERS_FILE = "users.json"
EVENTS_FILE = "events.json"

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class Event(BaseModel):
    id: str
    title: str
    start: str
    end: Optional[str] = None
    description: Optional[str] = None

app = FastAPI(title="SnapPlanner API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper functions
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def load_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_events(events):
    with open(EVENTS_FILE, 'w') as f:
        json.dump(events, f)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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
    except JWTError:
        raise credentials_exception
    
    users = load_users()
    if username not in users:
        raise credentials_exception
    return {"username": username}

# Routes
@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/login.html")

@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    user = users.get(form_data.username)
    
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

@app.post("/auth/register")
async def register(user_data: UserCreate):
    users = load_users()
    
    if user_data.username in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    users[user_data.username] = {
        'username': user_data.username,
        'password': hashed_password,
        'email': user_data.email
    }
    
    save_users(users)
    return {"message": "User created successfully"}

@app.get("/events/", response_model=List[Event])
async def get_user_events(current_user: User = Depends(get_current_user)):
    events = load_events()
    user_events = [e for e in events if e.get('user_id') == current_user['username']]
    return user_events

@app.post("/events/")
async def create_event(event: Event, current_user: User = Depends(get_current_user)):
    events = load_events()
    event_data = event.dict()
    event_data['user_id'] = current_user['username']
    events.append(event_data)
    save_events(events)
    return {"message": "Event created successfully"}

if __name__ == "__main__":
    uvicorn.run("FastAPI_local:app", host="0.0.0.0", port=8000, reload=True)