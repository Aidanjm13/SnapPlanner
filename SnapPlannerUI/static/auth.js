// Authentication state
let authToken = localStorage.getItem('authToken');

// Function to check if user is logged in
function isLoggedIn() {
    if (!authToken) return false;
    
    try {
        // Check if token is expired
        const payload = JSON.parse(atob(authToken.split('.')[1]));
        const now = Date.now() / 1000;
        if (payload.exp < now) {
            logout();
            return false;
        }
        return true;
    } catch (error) {
        console.error('Token validation error:', error);
        logout();
        return false;
    }
}

// Function to handle login
async function login(username, password) {
    if (!username || !password) {
        console.error('Username and password are required');
        return false;
    }
    
    try {
        const response = await fetch('/auth/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'username': username,
                'password': password,
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Login failed');
        }

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);
        
        return true;
    } catch (error) {
        console.error('Login error:', error);
        return false;
    }
}

// Function to handle registration
async function register(username, password, email) {
    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                password,
                email
            })
        });

        if (!response.ok) {
            throw new Error('Registration failed');
        }

        // After successful registration, automatically log in
        return await login(username, password);
    } catch (error) {
        console.error('Registration error:', error);
        return false;
    }
}

// Function to handle logout
function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
}

// Function to get authentication headers
function getAuthHeaders() {
    return {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
    };
}

// Export the functions
window.auth = {
    login,
    register,
    logout,
    isLoggedIn,
    getAuthHeaders
};