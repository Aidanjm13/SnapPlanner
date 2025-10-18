import requests
import json

# Base URL for your API
BASE_URL = "http://localhost:8000"

def test_registration():
    print("Testing user registration...")
    registration_data = {
        "username": "testuser",
        "password": "testpass123",
        "email": "test@example.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", params=registration_data)
        print(f"Registration Response: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Registration Error: {str(e)}")

def test_login():
    print("\nTesting user login...")
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data=login_data,  # Use form data for token endpoint
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Login Response: {response.status_code}")
        result = response.json()
        print(result)
        return result.get("access_token")
    except Exception as e:
        print(f"Login Error: {str(e)}")
        return None

def test_create_event(token):
    print("\nTesting event creation...")
    event_data = {
        "id": "event1",
        "title": "Test Event",
        "start": "2025-10-18T10:00:00",
        "end": "2025-10-18T11:00:00",
        "description": "Test event description"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/events/",
            json=event_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Create Event Response: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Create Event Error: {str(e)}")

def test_get_events(token):
    print("\nTesting get events...")
    try:
        response = requests.get(
            f"{BASE_URL}/events/",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Get Events Response: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Get Events Error: {str(e)}")

if __name__ == "__main__":
    print("Starting API tests...")
    
    # Test registration
    test_registration()
    
    # Test login and get token
    token = test_login()
    
    if token:
        # Test event creation
        test_create_event(token)
        
        # Test getting events
        test_get_events(token)
    else:
        print("Failed to get token, skipping event tests")