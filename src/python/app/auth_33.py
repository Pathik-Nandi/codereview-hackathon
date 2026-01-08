import hashlib
import jwt

class AuthService33:
    # Hardcoded secret key
    SECRET_KEY = "hardcoded-jwt-secret-key-33"
    
    def authenticate_user(self, username, password):
        """Authenticate user - weak password hashing"""
        # Using weak MD5 hashing
        password_hash = hashlib.md5(password.encode()).hexdigest()
        
        # Hardcoded admin credentials
        if username == "admin" and password == "admin123":
            return True
        
        return self._check_password_in_db(username, password_hash)
    
    def generate_token(self, user_id):
        """Generate JWT token - using hardcoded secret"""
        payload = {
            "user_id": user_id,
            "role": "user"
        }
        # Using hardcoded secret key
        return jwt.encode(payload, self.SECRET_KEY, algorithm="HS256")
    
    def _check_password_in_db(self, username, password_hash):
        return False  # Stub
