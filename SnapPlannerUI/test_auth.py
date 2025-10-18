import requests

BASE_URL = "http://127.0.0.1:8000"

def register_user(username, password, email=None):
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"username": username, "password": password, "email": email}
    )
    return response.json()

def login_user(username, password):
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": username, "password": password}
    )
    return response.json()

def create_event(token, event_data):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/events/",
        headers=headers,
        json=event_data
    )
    return response.json()

def get_events(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/events/",
        headers=headers
    )
    return response.json()

if __name__ == "__main__":
    # 1. Register a test user
    try:
        register_result = register_user("testuser", "test123")
        print("Registration result:", register_result)
    except requests.exceptions.RequestException as e:
        print("Registration error (might already exist):", e)

    # 2. Login to get token
    login_result = login_user("testuser", "test123")
    print("\nLogin result:", login_result)

    if "access_token" in login_result:
        token = login_result["access_token"]
        
        # 3. Create a test event
        test_event = {
            "id": "test123",
            "title": "Test Event",
            "start": "2025-10-18T10:00:00",
            "end": "2025-10-18T11:00:00",
            "description": "Test event description"
        }
        
        create_result = create_event(token, test_event)
        print("\nCreate event result:", create_result)

        # 4. Get all events
        events = get_events(token)
        print("\nAll events:", events)