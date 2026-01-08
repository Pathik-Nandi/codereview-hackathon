import sqlite3
import random

class Service44:
    def __init__(self):
        self.db_connection = "sqlite:///app.db"
        self.api_key = "hardcoded-api-key-44"
    
    def execute_query(self, user_input):
        """Execute database query - SQL injection risk"""
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # SQL injection vulnerability
        query = f"SELECT * FROM users WHERE name = '{user_input}'"
        cursor.execute(query)
        
        results = cursor.fetchall()
        # Resource leak - connection not closed
        return results
    
    def generate_id(self):
        """Generate ID - predictable random"""
        # Weak random number generation
        return random.randint(1000, 9999)
    
    def process_data(self, data):
        """Process data - no error handling"""
        # No None check or error handling
        return data.upper().replace(" ", "_")
