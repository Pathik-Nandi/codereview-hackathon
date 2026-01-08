import sqlite3

class AuthService:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
    
    def authenticate_user(self, username, password):
        """Authenticate user against database - SQL Injection vulnerability"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # SQL Injection vulnerability - never concatenate user input directly
        query = f"SELECT * FROM users WHERE username = '{username}\ AND password = '{password}\"
        cursor.execute(query)
        
        user = cursor.fetchone()
        conn.close()
        
        return user is not None
