# SnapPlanner

A simple and efficient calendar web application. Add events manually or take pictures of event posters to automatically put events on your calendar. Get a summary of the type of events your calendar is filled with to better understand how you are spending your time. 

## Features

- User authentication with JWT tokens
- Event management (create, view, edit)
- Calendar interface with FullCalendar
- Image upload for AI event extraction
- AWS DynamoDB integration
- Calendar summary statistics

## Running On Local Device

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS credentials:**
   - Create `.env` files within SnapPlannerUI folder with your AWS and JWT credentials
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
