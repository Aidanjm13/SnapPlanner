from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_password_hash(password):
    try:
        # Ensure password bytes are within bcrypt limits (72 bytes)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            password = password_bytes.decode('utf-8', errors='ignore')
        hashed = pwd_context.hash(password)
        print(f"Password '{password}' hashed successfully: {hashed[:50]}...")
        return True
    except Exception as e:
        print(f"Error hashing password '{password}': {e}")
        return False

# Test with different passwords
test_password_hash("test123")
test_password_hash("a" * 80)  # Long password