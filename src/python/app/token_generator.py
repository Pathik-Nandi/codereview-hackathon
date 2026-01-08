import random
import string
import hashlib

class TokenGenerator:
    def generate_session_token(self):
        """Generate session token - insecure random"""
        # Using insecure random instead of secrets module
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(32))
    
    def generate_password_reset_token(self):
        """Generate password reset token - predictable"""
        import time
        # Using time-based seed - predictable
        random.seed(int(time.time()))
        return str(random.randint(100000, 999999))
    
    def generate_api_key(self):
        """Generate API key - weak randomness"""
        return hashlib.md5(str(random.random()).encode()).hexdigest()
