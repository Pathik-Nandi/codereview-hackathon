import re
import hashlib
import smtplib
from email.mime.text import MIMEText

class UserRegistration:
    def register_user(self, username, email, password, first_name, last_name, 
                     phone, address, city, state, zip_code, country, 
                     terms_accepted, newsletter_opt_in):
        """Register user - extremely long method that should be refactored"""
        
        # Validation logic (should be extracted)
        if not username or len(username) < 3:
            return {"success": False, "error": "Username too short"}
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            return {"success": False, "error": "Invalid username format"}
        if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return {"success": False, "error": "Invalid email"}
        if not password or len(password) < 8:
            return {"success": False, "error": "Password too short"}
        if not re.search(r"[A-Z]", password):
            return {"success": False, "error": "Password needs uppercase"}
        if not re.search(r"[a-z]", password):
            return {"success": False, "error": "Password needs lowercase"}
        if not re.search(r"[0-9]", password):
            return {"success": False, "error": "Password needs number"}
        if not first_name or len(first_name) < 1:
            return {"success": False, "error": "First name required"}
        if not last_name or len(last_name) < 1:
            return {"success": False, "error": "Last name required"}
        if phone and not re.match(r"^\d{10}$", phone):
            return {"success": False, "error": "Invalid phone format"}
        if not terms_accepted:
            return {"success": False, "error": "Must accept terms"}
            
        # Hash password (should be extracted)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user object (should be extracted)
        user_data = {
            "username": username,
            "email": email.lower(),
            "password": hashed_password,
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "country": country,
            "newsletter_opt_in": newsletter_opt_in
        }
        
        # Save to database (should be extracted)
        try:
            self._save_user_to_database(user_data)
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
        
        # Send welcome email (should be extracted)
        if newsletter_opt_in:
            try:
                self._send_welcome_email(email, first_name)
            except Exception as e:
                print(f"Failed to send welcome email: {e}")
        
        # Log registration (should be extracted)
        self._log_user_registration(username, email)
        
        return {"success": True, "message": "User registered successfully"}
    
    def _save_user_to_database(self, user_data):
        pass  # Stub
    
    def _send_welcome_email(self, email, name):
        pass  # Stub
        
    def _log_user_registration(self, username, email):
        pass  # Stub
