# Authentication System Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Ensure Application is Running

```bash
# The application should already be running
# Check the logs for:
# [info] Authentication service initialized jwt_expiration_hours=24
```

### Step 2: Register Your First User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123456",
    "full_name": "Administrator"
  }'
```

**✅ Expected:** User created with `user_id: 1`

### Step 3: Login and Get Token

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123456"
  }'
```

**✅ Expected:** JWT token in response
```json
{
  "session": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    ...
  }
}
```

### Step 4: Save Token for Future Use

```bash
# Copy the token from the response
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step 5: Use Token in Requests

```bash
# Validate your token
curl -X GET http://localhost:5000/api/auth/validate \
  -H "Authorization: Bearer $TOKEN"

# Use token with any protected endpoint
curl -X POST http://localhost:5000/api/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repository": "owner/repo", "pr_number": 123}'
```

---

## 📊 Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

1️⃣ REGISTRATION
   ┌──────────┐     POST /api/auth/register      ┌──────────┐
   │  Client  │ ────────────────────────────────> │  Server  │
   └──────────┘     {username, email, password}   └──────────┘
                                                        │
                                                        ▼
                                                   Hash Password
                                                        │
                                                        ▼
                                                 ┌──────────────┐
                                                 │   Database   │
                                                 │  users table │
                                                 └──────────────┘
                                                        │
   ┌──────────┐     201 Created                       │
   │  Client  │ <───────────────────────────────────────
   └──────────┘     {user_id, username, email}


2️⃣ LOGIN
   ┌──────────┐     POST /api/auth/login         ┌──────────┐
   │  Client  │ ────────────────────────────────> │  Server  │
   └──────────┘     {email, password}             └──────────┘
                                                        │
                                                        ▼
                                                  Verify Password
                                                        │
                                                        ▼
                                                  Generate JWT
                                                        │
                                                        ▼
                                                 ┌──────────────────┐
                                                 │    Database      │
                                                 │ user_sessions    │
                                                 │ table (save)     │
                                                 └──────────────────┘
                                                        │
   ┌──────────┐     200 OK                            │
   │  Client  │ <───────────────────────────────────────
   └──────────┘     {token, user_id, expires_at}
        │
        ▼
   Save Token
   for future use


3️⃣ AUTHENTICATED REQUEST
   ┌──────────┐     POST /api/analyze              ┌──────────┐
   │  Client  │ ─────────────────────────────────> │  Server  │
   └──────────┘     Authorization: Bearer <token>  └──────────┘
                                                         │
                                                         ▼
                                                 @require_auth
                                                 validates token
                                                         │
                                                         ▼
                                                  ┌──────────────┐
                                                  │   Database   │
                                                  │ Check active │
                                                  │   session    │
                                                  └──────────────┘
                                                         │
                                                         ▼
                                                   Token Valid?
                                                    /        \
                                              YES  /          \  NO
                                                  ▼            ▼
   ┌──────────┐     200 OK              Process    401 Unauthorized
   │  Client  │ <──────────────────   Request      ────────────────>
   └──────────┘     {analysis data}                   {error}


4️⃣ LOGOUT
   ┌──────────┐     POST /api/auth/logout         ┌──────────┐
   │  Client  │ ────────────────────────────────> │  Server  │
   └──────────┘     Authorization: Bearer <token>  └──────────┘
                                                         │
                                                         ▼
                                                  ┌──────────────────┐
                                                  │    Database      │
                                                  │ Mark session as  │
                                                  │ inactive         │
                                                  └──────────────────┘
                                                         │
   ┌──────────┐     200 OK                            │
   │  Client  │ <───────────────────────────────────────
   └──────────┘     {success: true}
        │
        ▼
   Clear Token
```

---

## 🔐 Security Checklist

Before deploying to production:

```
☐ Change JWT_SECRET_KEY in .env to a secure random string
☐ Use HTTPS/TLS for all API communications
☐ Set strong password requirements (current: 8 chars minimum)
☐ Configure JWT_EXPIRATION_HOURS appropriately
☐ Enable database backups
☐ Set up monitoring for failed login attempts
☐ Review and restrict API rate limits
☐ Use environment-specific .env files
☐ Never commit .env file to version control
☐ Rotate JWT secret keys periodically
```

---

## 🧪 Testing Checklist

Test these scenarios:

```
✅ Register new user with valid data
✅ Register with duplicate username (should fail)
✅ Register with duplicate email (should fail)
✅ Register with weak password (should fail)
✅ Login with correct credentials
✅ Login with wrong password (should fail)
✅ Login with non-existent email (should fail)
✅ Access protected endpoint with valid token
✅ Access protected endpoint without token (should fail)
✅ Access protected endpoint with expired token (should fail)
✅ Logout and verify token is invalidated
✅ Try to use token after logout (should fail)
```

---

## 📋 Common Commands

### User Management

```bash
# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","email":"user1@example.com","password":"pass123456"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@example.com","password":"pass123456"}'

# Validate token
curl -X GET http://localhost:5000/api/auth/validate \
  -H "Authorization: Bearer $TOKEN"

# List sessions
curl -X GET http://localhost:5000/api/auth/sessions \
  -H "Authorization: Bearer $TOKEN"

# Logout
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

### Database Queries

```sql
-- List all users
SELECT id, username, email, created_at, last_login FROM users;

-- List active sessions
SELECT s.id, u.username, s.created_at, s.expires_at, s.last_activity
FROM user_sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = true;

-- Count users
SELECT COUNT(*) FROM users;

-- Count active sessions
SELECT COUNT(*) FROM user_sessions WHERE is_active = true;
```

---

## 🐍 Python Integration Example

```python
import requests

class AuthClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.token = None
    
    def register(self, username, email, password, full_name=None):
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        return response.json()
    
    def login(self, email, password):
        """Login and store token."""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"email": email, "password": password}
        )
        data = response.json()
        if data.get('success'):
            self.token = data['session']['token']
        return data
    
    def logout(self):
        """Logout and clear token."""
        if not self.token:
            return {"error": "Not logged in"}
        
        response = requests.post(
            f"{self.base_url}/api/auth/logout",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.token = None
        return response.json()
    
    def validate(self):
        """Validate current token."""
        if not self.token:
            return {"error": "Not logged in"}
        
        response = requests.get(
            f"{self.base_url}/api/auth/validate",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.json()
    
    def analyze_pr(self, repository, pr_number):
        """Analyze PR (requires authentication)."""
        if not self.token:
            return {"error": "Not logged in"}
        
        response = requests.post(
            f"{self.base_url}/api/analyze",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"repository": repository, "pr_number": pr_number}
        )
        return response.json()

# Usage
client = AuthClient()

# Register
print(client.register("alice", "alice@example.com", "alice123456", "Alice"))

# Login
print(client.login("alice@example.com", "alice123456"))

# Validate
print(client.validate())

# Analyze PR (authenticated)
print(client.analyze_pr("owner/repo", 123))

# Logout
print(client.logout())
```

---

## 📞 Support & Troubleshooting

### Application Logs
Check logs for authentication-related messages:
```bash
# Look for these log messages:
[info] Authentication service initialized jwt_expiration_hours=24
[info] User registered successfully user_id=1 username=alice
[info] User logged in successfully user_id=1 username=alice
```

### Database Connection Issues
```bash
# Test database connection
./setup_database.sh

# Check if tables exist
psql -U postgres -d pr_analysis -p 5433 -c "\dt"
```

### Token Issues
```bash
# Check token expiration
# JWT tokens expire after JWT_EXPIRATION_HOURS (default: 24)
# Login again to get a fresh token
```

---

## 🎯 Quick Reference

| Action | Endpoint | Method | Auth Required |
|--------|----------|--------|---------------|
| Register | `/api/auth/register` | POST | ❌ |
| Login | `/api/auth/login` | POST | ❌ |
| Logout | `/api/auth/logout` | POST | ✅ |
| Validate Token | `/api/auth/validate` | GET | ✅ |
| List Sessions | `/api/auth/sessions` | GET | ✅ |

---

**Ready to use! 🎉**

For detailed documentation, see: `documentation/AUTHENTICATION.md`
