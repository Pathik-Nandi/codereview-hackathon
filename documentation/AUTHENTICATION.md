# Authentication System Documentation

## Overview

The PR Review System now includes a complete user authentication system with JWT token-based authentication, secure password hashing, and session management.

## Features

✅ **User Registration** - Create new user accounts with username, email, and password  
✅ **User Login** - Authenticate users and generate JWT tokens  
✅ **User Logout** - Invalidate user sessions  
✅ **Session Management** - Track active user sessions with expiration  
✅ **JWT Token Validation** - Secure API endpoints with JWT authentication  
✅ **Password Security** - Bcrypt password hashing  
✅ **Configurable JWT Secret** - Environment-based secret key configuration  

---

## Database Schema

### Users Table
Stores user account information.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key, auto-increment |
| username | String(100) | Unique username, indexed |
| email | String(255) | Unique email address, indexed |
| password_hash | String(255) | Bcrypt hashed password |
| full_name | String(255) | Optional full name |
| is_active | Boolean | Account active status (default: true) |
| is_admin | Boolean | Admin flag (default: false) |
| created_at | DateTime | Account creation timestamp |
| updated_at | DateTime | Last update timestamp |
| last_login | DateTime | Last successful login |

**Indexes:**
- `idx_user_email_active` on (email, is_active)
- `idx_user_username_active` on (username, is_active)

### User Sessions Table
Tracks active login sessions.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key, auto-increment |
| user_id | Integer | Foreign key to users table |
| session_token | String(500) | JWT token (unique, indexed) |
| ip_address | String(50) | Client IP address |
| user_agent | String(500) | Client user agent string |
| is_active | Boolean | Session active status |
| created_at | DateTime | Session creation time |
| expires_at | DateTime | Token expiration time, indexed |
| last_activity | DateTime | Last API activity timestamp |
| logged_out_at | DateTime | Logout timestamp (if logged out) |

**Indexes:**
- `idx_session_token_active` on (session_token, is_active)
- `idx_session_user_active` on (user_id, is_active)
- `idx_session_expires` on (expires_at, is_active)

---

## Configuration

### Environment Variables (.env)

Add these configuration variables to your `.env` file:

```bash
# JWT Authentication Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-use-at-least-32-characters
JWT_EXPIRATION_HOURS=24
JWT_ALGORITHM=HS256
```

**Important Security Notes:**
- ⚠️ **CHANGE the JWT_SECRET_KEY in production!**
- Generate a secure key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Never commit the `.env` file with production secrets to version control
- Use at least 32 characters for the secret key

### Configuration in Code

The authentication service automatically reads configuration from:
1. Environment variables (`.env` file)
2. `config/settings.yaml` file (fallback)

---

## API Endpoints

### 1. Register User

**Endpoint:** `POST /api/auth/register`

**Description:** Create a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Required Fields:**
- `username` (unique, alphanumeric)
- `email` (unique, valid email format)
- `password` (minimum 8 characters)

**Optional Fields:**
- `full_name`

**Success Response (201):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "created_at": "2025-12-21T10:30:00"
  }
}
```

**Error Response (400):**
```json
{
  "success": false,
  "error": "Username already exists"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

---

### 2. Login User

**Endpoint:** `POST /api/auth/login`

**Description:** Authenticate a user and receive a JWT token.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "session": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "expires_at": "2025-12-22T10:30:00",
    "session_id": 123
  }
}
```

**Error Response (401):**
```json
{
  "success": false,
  "error": "Invalid email or password"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

**Store the token for subsequent authenticated requests:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 3. Logout User

**Endpoint:** `POST /api/auth/logout`

**Description:** Logout a user and invalidate their session.

**Headers:**
```
Authorization: Bearer <token>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

**Error Response (401):**
```json
{
  "error": "Invalid or expired token. Please login again."
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4. Validate Token

**Endpoint:** `GET /api/auth/validate`

**Description:** Validate the current JWT token and get user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Success Response (200):**
```json
{
  "valid": true,
  "user": {
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_admin": false
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/auth/validate \
  -H "Authorization: Bearer $TOKEN"
```

---

### 5. Get User Sessions

**Endpoint:** `GET /api/auth/sessions`

**Description:** Get all active sessions for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Success Response (200):**
```json
{
  "sessions": [
    {
      "session_id": 123,
      "created_at": "2025-12-21T10:30:00",
      "expires_at": "2025-12-22T10:30:00",
      "last_activity": "2025-12-21T15:45:00",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
    }
  ]
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/auth/sessions \
  -H "Authorization: Bearer $TOKEN"
```

---

## Protecting API Endpoints

### Using the `@require_auth` Decorator

To protect an endpoint and require authentication, use the `@require_auth` decorator:

```python
from main import require_auth

@app.route('/api/protected-endpoint', methods=['GET'])
@require_auth
def protected_endpoint():
    """This endpoint requires authentication."""
    # Access current user data
    user_data = request.current_user
    
    return jsonify({
        'message': f"Hello {user_data['username']}!",
        'user_id': user_data['user_id']
    }), 200
```

### Accessing Current User

When using the `@require_auth` decorator, the current user's data is available in `request.current_user`:

```python
{
  'user_id': 1,
  'username': 'john_doe',
  'email': 'john@example.com',
  'full_name': 'John Doe',
  'is_admin': False
}
```

---

## Complete Usage Example

### 1. Register a New User

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "alicepassword123",
    "full_name": "Alice Johnson"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "user_id": 2,
    "username": "alice",
    "email": "alice@example.com",
    "full_name": "Alice Johnson",
    "created_at": "2025-12-21T10:30:00"
  }
}
```

### 2. Login

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "alicepassword123"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "session": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6ImFsaWNlIiwiZW1haWwiOiJhbGljZUBleGFtcGxlLmNvbSIsImV4cCI6MTY3MTcxMTAwMCwiaWF0IjoxNjcxNjI0NjAwfQ.xyz123",
    "user_id": 2,
    "username": "alice",
    "email": "alice@example.com",
    "full_name": "Alice Johnson",
    "expires_at": "2025-12-22T10:30:00",
    "session_id": 456
  }
}
```

**Save the token:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Use Token for Authenticated Requests

```bash
# Validate token
curl -X GET http://localhost:5000/api/auth/validate \
  -H "Authorization: Bearer $TOKEN"

# Get user sessions
curl -X GET http://localhost:5000/api/auth/sessions \
  -H "Authorization: Bearer $TOKEN"

# Access protected PR analysis endpoint
curl -X POST http://localhost:5000/api/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "owner/repo",
    "pr_number": 123
  }'
```

### 4. Logout

```bash
# Logout
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:5000"

# 1. Register a user
register_data = {
    "username": "bob",
    "email": "bob@example.com",
    "password": "bobpassword123",
    "full_name": "Bob Smith"
}

response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
print("Register:", response.json())

# 2. Login
login_data = {
    "email": "bob@example.com",
    "password": "bobpassword123"
}

response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
session = response.json()['session']
token = session['token']
print("Login:", session)

# 3. Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}

# Validate token
response = requests.get(f"{BASE_URL}/api/auth/validate", headers=headers)
print("Validate:", response.json())

# Analyze PR (with authentication)
pr_data = {
    "repository": "owner/repo",
    "pr_number": 123
}
response = requests.post(f"{BASE_URL}/api/analyze", json=pr_data, headers=headers)
print("PR Analysis:", response.json())

# 4. Logout
response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
print("Logout:", response.json())
```

---

## Security Features

### 1. Password Security
- ✅ **Bcrypt Hashing** - Industry-standard password hashing
- ✅ **Automatic Salt Generation** - Each password gets a unique salt
- ✅ **Minimum Length** - 8 character minimum enforced
- ✅ **Never Stored Plain Text** - Only hashed passwords in database

### 2. JWT Token Security
- ✅ **Configurable Secret** - Environment-based secret key
- ✅ **Token Expiration** - Configurable expiration time (default 24 hours)
- ✅ **HS256 Algorithm** - Secure HMAC signing
- ✅ **Session Validation** - Token validated against active sessions

### 3. Session Management
- ✅ **Active Session Tracking** - All sessions tracked in database
- ✅ **Automatic Expiration** - Sessions expire after configured time
- ✅ **Multiple Device Support** - Users can have multiple active sessions
- ✅ **Session Invalidation** - Logout immediately invalidates session
- ✅ **Last Activity Tracking** - Track when session was last used

### 4. Database Security
- ✅ **Unique Constraints** - Username and email must be unique
- ✅ **Indexed Queries** - Optimized for fast lookups
- ✅ **Foreign Key Cascade** - Sessions deleted when user is deleted
- ✅ **Account Status** - `is_active` flag for account management

---

## Session Cleanup

Expired sessions can be cleaned up using the auth service:

```python
from services.auth_service import AuthService
from services.database_service import DatabaseService

db_service = DatabaseService()
auth_service = AuthService(db_service)

# Clean up expired sessions
count = auth_service.cleanup_expired_sessions()
print(f"Cleaned up {count} expired sessions")
```

This can be scheduled as a periodic task (e.g., using Celery or cron).

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created (user registered) |
| 400 | Bad Request (invalid input) |
| 401 | Unauthorized (invalid credentials or token) |
| 403 | Forbidden (insufficient permissions) |
| 503 | Service Unavailable (auth service not initialized) |

---

## Troubleshooting

### "Authentication service not available"
- Ensure database is configured and running
- Check `database.enabled: true` in config
- Verify database connection in `.env` file

### "Invalid or expired token"
- Token has expired (default 24 hours)
- User has logged out
- JWT secret key changed
- Solution: Login again to get a new token

### "Username already exists"
- Choose a different username
- Usernames must be unique across the system

### "Email already registered"
- Email is already in use
- Use a different email address
- If you forgot your password, implement password reset flow

### "Password must be at least 8 characters"
- Use a password with 8 or more characters
- Consider using a strong password with mixed characters

---

## Next Steps

### Recommended Enhancements

1. **Password Reset Flow**
   - Email-based password reset
   - Temporary reset tokens

2. **Email Verification**
   - Send verification email on registration
   - Verify email before allowing login

3. **Rate Limiting**
   - Limit login attempts per IP
   - Prevent brute force attacks

4. **Two-Factor Authentication (2FA)**
   - TOTP-based 2FA
   - SMS-based verification

5. **OAuth Integration**
   - GitHub OAuth login
   - Google/Microsoft SSO

6. **API Key Management**
   - Generate API keys for service accounts
   - Programmatic API access

7. **Admin Dashboard**
   - User management interface
   - Session monitoring
   - Account activation/deactivation

---

## Support

For issues or questions about the authentication system:
1. Check the logs in the application output
2. Review this documentation
3. Check database connectivity
4. Verify environment configuration in `.env`

---

**Last Updated:** December 21, 2025  
**Version:** 1.0.0  
**Author:** PR Review System Team
