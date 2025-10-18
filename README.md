# SnapPlanner

A calendar web application with AWS Cognito authentication and DynamoDB storage.

## Features

- User authentication with JWT tokens
- Event management (create, view, edit)
- Calendar interface with FullCalendar
- Image upload for event extraction
- AWS DynamoDB integration

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS credentials:**
   - Update `.env` files with your AWS credentials
   - Never commit real credentials to version control

3. **Setup DynamoDB tables:**
   ```bash
   cd SnapPlannerUI
   python setup_db.py
   ```

4. **Run the application:**
   ```bash
   cd SnapPlannerUI
   python FastAPI.py
   ```

5. **Access the application:**
   - Open http://localhost:8000 in your browser

## Security Notes

- AWS credentials are stored in `.env` files (not committed)
- JWT tokens expire after 30 minutes
- CORS is configured for localhost only
- Input validation on all API endpoints

## API Endpoints

- `POST /auth/token` - Login
- `POST /auth/register` - Register new user
- `GET /events/` - Get user events
- `POST /events/` - Create new event
- `POST /uploadfile/` - Upload image for processing

## Project Structure

```
SnapPlanner/
├── SnapPlannerUI/
│   ├── static/          # Frontend files
│   ├── uploads/         # Temporary file storage
│   ├── FastAPI.py       # Main backend application
│   ├── setup_db.py      # Database setup script
│   └── .env             # Environment variables
├── requirements.txt     # Python dependencies
└── README.md           # This file
```