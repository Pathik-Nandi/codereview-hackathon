import hashlib
import base64
from Crypto.Cipher import DES

class CryptoUtils:
    def hash_password(self, password):
        """Hash password - using weak MD5"""
        return hashlib.md5(password.encode()).hexdigest()
    
    def hash_sensitive_data(self, data):
        """Hash sensitive data - using deprecated SHA1"""
        return hashlib.sha1(data.encode()).hexdigest()
    
    def encrypt_data(self, data, key):
        """Encrypt data - using weak DES encryption"""
        # DES is deprecated and insecure
        cipher = DES.new(key[:8].encode(), DES.MODE_ECB)
        # Padding data to 8 bytes
        padded_data = data + ' ' * (8 - len(data) % 8)
        encrypted = cipher.encrypt(padded_data.encode())
        return base64.b64encode(encrypted).decode()
    
    def generate_simple_hash(self, text):
        """Generate simple hash - custom weak algorithm"""
        # Custom weak hashing algorithm
        result = 0
        for char in text:
            result = (result + ord(char)) * 37
        return str(result)
