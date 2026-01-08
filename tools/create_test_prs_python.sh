#!/bin/bash

###############################################################################
# Test PR Creation Script - Python Edition
#
# Creates 50 test PRs with various Python scenarios for code review testing
# Covers: security issues, code quality, performance, style, complexity, etc.
#
# Usage:
#   ./tools/create_test_prs_python.sh
#
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_PATH="/home/pathiknandi/Desktop/Code_Review_System/codereview-hackathon"
REPO_NAME="Pathik-Nandi/codereview-hackathon"
BASE_BRANCH="main"

echo "================================================================================"
echo -e "${BLUE}🐍 PYTHON TEST PR CREATION SCRIPT${NC}"
echo "================================================================================"
echo -e "Repository:      ${YELLOW}$REPO_NAME${NC}"
echo -e "Local Path:      ${YELLOW}$REPO_PATH${NC}"
echo -e "Base Branch:     ${YELLOW}$BASE_BRANCH${NC}"
echo -e "PRs to Create:   ${YELLOW}50${NC}"
echo "================================================================================"
echo ""

# Check if directory exists
if [ ! -d "$REPO_PATH" ]; then
    echo -e "${RED}❌ Error: Directory $REPO_PATH does not exist${NC}"
    exit 1
fi

cd "$REPO_PATH" || exit 1

# Check if it's a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: $REPO_PATH is not a git repository${NC}"
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ Error: GitHub CLI (gh) is not installed${NC}"
    echo -e "${YELLOW}Install it with: sudo apt install gh${NC}"
    exit 1
fi

# Check for GitHub token authentication
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ Error: GITHUB_TOKEN environment variable not set${NC}"
    echo -e "${YELLOW}Set your token with: export GITHUB_TOKEN=your_github_token_here${NC}"
    exit 1
fi

# Authenticate gh CLI with token
echo "$GITHUB_TOKEN" | gh auth login --with-token

# Verify authentication worked
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Error: Failed to authenticate with provided token${NC}"
    exit 1
fi

# Ensure we're on main and it's up to date
echo -e "${BLUE}🔄 Updating main branch...${NC}"
git checkout main
git pull origin main

# Counter
SUCCESS_COUNT=0
FAILURE_COUNT=0

echo ""
echo -e "${GREEN}Starting Python PR creation...${NC}"
echo ""

# Function to create PR
create_pr() {
    local PR_NUM=$1
    local TITLE=$2
    local DESCRIPTION=$3
    local FILE_CHANGES=$4
    
    BRANCH_NAME="test/python-pr-${PR_NUM}"
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🐍 Creating Python PR #${PR_NUM}: ${TITLE}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Create and checkout branch
    git checkout -b "$BRANCH_NAME" main 2>/dev/null || git checkout "$BRANCH_NAME"
    
    # Create directory structure
    mkdir -p src/python/app
    
    # Apply file changes (passed as string to be evaluated)
    eval "$FILE_CHANGES"
    
    # Commit changes
    git add .
    git commit -m "$TITLE" -m "$DESCRIPTION"
    
    # Push branch
    if git push -u origin "$BRANCH_NAME" --force; then
        # Create PR
        if gh pr create --title "$TITLE" --body "$DESCRIPTION" --base main --head "$BRANCH_NAME"; then
            echo -e "${GREEN}✅ PR created successfully${NC}"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo -e "${RED}❌ Failed to create PR${NC}"
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
        fi
    else
        echo -e "${RED}❌ Failed to push branch${NC}"
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi
    
    # Go back to main
    git checkout main
    
    echo ""
}

# PR 1: SQL Injection Vulnerability
create_pr 1 "Add user authentication system" \
"Implements basic user login with database lookup" \
'cat > src/python/app/auth_service.py << '\''EOF'\''
import sqlite3

class AuthService:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
    
    def authenticate_user(self, username, password):
        """Authenticate user against database - SQL Injection vulnerability"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # SQL Injection vulnerability - never concatenate user input directly
        query = f"SELECT * FROM users WHERE username = '\'''{username}'\'' AND password = '\'''{password}'\''"
        cursor.execute(query)
        
        user = cursor.fetchone()
        conn.close()
        
        return user is not None
EOF'

# PR 2: Hardcoded Secrets and Credentials
create_pr 2 "Add database and API configuration" \
"Sets up database connection and external API integration" \
'cat > src/python/app/config.py << '\''EOF'\''
import os

class Config:
    """Configuration class with hardcoded secrets - security issue"""
    
    # Hardcoded database credentials
    DATABASE_URL = "postgresql://admin:SuperSecret123@localhost:5432/myapp"
    
    # Hardcoded API keys
    AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
    AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    
    # Social media API keys
    TWITTER_API_KEY = "xvz1evFS4wEEPTGEFPHBog"
    TWITTER_SECRET = "L8qq9PZyRg6ieKGEKhZolGC0vJWLw8iEJ88DRdyOg"
    
    # Payment gateway
    STRIPE_SECRET_KEY = "sk_test_26PHem9AhJZvU623DfE1x4sd"
    
    def get_db_connection(self):
        return self.DATABASE_URL
EOF'

# PR 3: None/Null Reference Errors
create_pr 3 "Add user profile management" \
"Implements user profile retrieval and display" \
'cat > src/python/app/profile_service.py << '\''EOF'\''
class ProfileService:
    def get_user_email(self, user):
        """Get user email - potential AttributeError if user is None"""
        return user.email.lower()  # No None check
    
    def get_full_name(self, user):
        """Get full name - multiple None reference risks"""
        return f"{user.first_name} {user.last_name}"  # No None checks
    
    def get_user_age(self, user):
        """Calculate age - potential errors"""
        from datetime import date
        return (date.today() - user.birth_date).days // 365
    
    def format_address(self, user):
        """Format address - chain of potential None references"""
        return f"{user.address.street}, {user.address.city}, {user.address.country}"
EOF'

# PR 4: Resource Leaks - Unclosed Files
create_pr 4 "Add file processing functionality" \
"Implements file upload and data processing" \
'cat > src/python/app/file_processor.py << '\''EOF'\''
import json
import csv

class FileProcessor:
    def process_json_file(self, file_path):
        """Process JSON file - resource leak, file not closed properly"""
        file = open(file_path, '\''r'\'')
        data = json.load(file)
        # File not closed - resource leak
        
        return len(data) if data else 0
    
    def read_csv_file(self, file_path):
        """Read CSV file - another resource leak"""
        file = open(file_path, '\''r'\'')
        reader = csv.reader(file)
        rows = list(reader)
        # File handle not closed
        
        return rows
    
    def write_log(self, message, log_file="app.log"):
        """Write to log - resource not properly managed"""
        log = open(log_file, '\''a'\'')
        log.write(f"{message}\n")
        # Log file not closed
EOF'

# PR 5: High Cyclomatic Complexity
create_pr 5 "Add complex order validation system" \
"Implements comprehensive order processing with validation" \
'cat > src/python/app/order_processor.py << '\''EOF'\''
class OrderProcessor:
    def process_order(self, order):
        """Process order with high cyclomatic complexity - needs refactoring"""
        if order is not None:
            if order.get('\''amount'\'') is not None and order['\''amount'\''] > 0:
                if order.get('\''customer'\'') is not None:
                    customer = order['\''customer'\'']
                    if customer.get('\''verified'\'') is True:
                        if order.get('\''items'\'') is not None and len(order['\''items'\'']) > 0:
                            for item in order['\''items'\'']:
                                if item.get('\''quantity'\'') is not None and item['\''quantity'\''] > 0:
                                    if item.get('\''price'\'') is not None and item['\''price'\''] > 0:
                                        if item.get('\''available'\'') is True:
                                            if order.get('\''shipping_address'\'') is not None:
                                                if order.get('\''payment_method'\'') is not None:
                                                    payment = order['\''payment_method'\'']
                                                    if payment.get('\''type'\'') in ['\''credit_card'\'', '\''debit_card'\'', '\''paypal'\'']:
                                                        if payment.get('\''validated'\'') is True:
                                                            return self._execute_order(order)
        return False
    
    def _execute_order(self, order):
        return True
EOF'

# PR 6: Unused Imports and Variables
create_pr 6 "Add string utility functions" \
"Implements helper functions for string manipulation" \
'cat > src/python/app/string_utils.py << '\''EOF'\''
import os
import sys
import json
import datetime
import re
import hashlib
import base64
import urllib.parse
from collections import defaultdict, Counter
from functools import reduce
import itertools

class StringUtils:
    def capitalize_words(self, text):
        """Capitalize words - many unused imports and variables"""
        unused_var = "this is not used"
        another_unused = 42
        temp_dict = {}
        
        if text is None or text == "":
            return text
            
        return " ".join(word.capitalize() for word in text.split())
    
    def clean_string(self, input_str):
        """Clean string - more unused variables"""
        pattern = r"[^a-zA-Z0-9\s]"
        unused_list = [1, 2, 3, 4, 5]
        temp_counter = 0
        
        return re.sub(pattern, "", input_str) if input_str else ""
EOF'

# PR 7: Thread Safety Issues
create_pr 7 "Add request counter service" \
"Implements a counter for tracking application requests" \
'cat > src/python/app/counter_service.py << '\''EOF'\''
import threading
import time

class CounterService:
    def __init__(self):
        self.count = 0
        self.request_times = []
    
    def increment(self):
        """Increment counter - race condition, not thread-safe"""
        current = self.count
        time.sleep(0.001)  # Simulate some processing
        self.count = current + 1
    
    def add_request_time(self, timestamp):
        """Add request time - not thread-safe list operation"""
        self.request_times.append(timestamp)
    
    def get_stats(self):
        """Get statistics - potential race conditions"""
        return {
            '\''total_requests'\'': self.count,
            '\''avg_requests_per_minute'\'': len(self.request_times) / 60 if self.request_times else 0
        }
EOF'

# PR 8: Empty Exception Blocks
create_pr 8 "Add error handling utilities" \
"Implements error handling and logging functionality" \
'cat > src/python/app/error_handler.py << '\''EOF'\''
import json
import requests

class ErrorHandler:
    def read_config_file(self, config_path):
        """Read configuration - empty exception handling"""
        try:
            with open(config_path, '\''r'\'') as f:
                return json.load(f)
        except:
            pass  # Empty exception block - bad practice
    
    def make_api_call(self, url, data):
        """Make API call - swallowing exceptions"""
        try:
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            pass  # Exception swallowed, no logging or handling
    
    def parse_integer(self, value):
        """Parse integer - silent failure"""
        try:
            return int(value)
        except:
            return None  # No logging of the error
EOF'

# PR 9: Magic Numbers and Hardcoded Values
create_pr 9 "Add validation utilities" \
"Implements input validation with business rules" \
'cat > src/python/app/validator.py << '\''EOF'\''
import re

class Validator:
    def validate_age(self, age):
        """Validate age - magic numbers without constants"""
        return 18 <= age <= 120  # Magic numbers
    
    def validate_password(self, password):
        """Validate password - hardcoded rules"""
        if not password or len(password) < 8:  # Magic number
            return False
        if len(password) > 64:  # Magic number
            return False
        return True
    
    def validate_phone(self, phone):
        """Validate phone number - magic pattern"""
        if not phone or len(phone) != 10:  # Magic number
            return False
        return phone.isdigit()
    
    def validate_credit_card(self, card_number):
        """Validate credit card - magic numbers"""
        if not card_number:
            return False
        # Remove spaces and dashes
        clean_number = re.sub(r"[\s-]", "", card_number)
        return len(clean_number) == 16 and clean_number.isdigit()  # Magic number
EOF'

# PR 10: Code Duplication
create_pr 10 "Add payment processing system" \
"Implements multiple payment methods with processing logic" \
'cat > src/python/app/payment_service.py << '\''EOF'\''
import hashlib
import hmac

class PaymentService:
    def process_credit_card(self, card_number, amount, cvv):
        """Process credit card payment - duplicated validation logic"""
        if not card_number or len(card_number.replace(" ", "")) != 16:
            print("Invalid card number")
            return False
        
        if not amount or amount <= 0:
            print("Invalid amount")
            return False
            
        if not cvv or len(cvv) != 3:
            print("Invalid CVV")
            return False
            
        print("Processing credit card payment...")
        return self._charge_card(card_number, amount)
    
    def process_debit_card(self, card_number, amount, pin):
        """Process debit card payment - same validation duplicated"""
        if not card_number or len(card_number.replace(" ", "")) != 16:
            print("Invalid card number")
            return False
        
        if not amount or amount <= 0:
            print("Invalid amount")
            return False
            
        if not pin or len(pin) != 4:
            print("Invalid PIN")
            return False
            
        print("Processing debit card payment...")
        return self._charge_card(card_number, amount)
    
    def _charge_card(self, card_number, amount):
        return True  # Simulated success
EOF'

# PR 11: Missing None/Null Checks
create_pr 11 "Add data processing utilities" \
"Implements data manipulation and processing functions" \
'cat > src/python/app/data_processor.py << '\''EOF'\''
class DataProcessor:
    def get_string_length(self, text):
        """Get string length - no None check"""
        return len(text)  # Potential TypeError if text is None
    
    def reverse_string(self, text):
        """Reverse string - no validation"""
        return text[::-1]  # TypeError if text is None
    
    def extract_numbers(self, text):
        """Extract numbers from text - no None checking"""
        import re
        return re.findall(r'\d+', text)  # TypeError if text is None
    
    def process_list(self, items):
        """Process list - no None or empty checks"""
        return [item.upper() for item in items]  # Multiple potential errors
    
    def get_dict_value(self, data, key):
        """Get dictionary value - no validation"""
        return data[key].strip()  # Multiple potential errors
EOF'

# PR 12: Insecure Random Number Generation
create_pr 12 "Add token and session management" \
"Generates secure tokens and manages user sessions" \
'cat > src/python/app/token_generator.py << '\''EOF'\''
import random
import string
import hashlib

class TokenGenerator:
    def generate_session_token(self):
        """Generate session token - insecure random"""
        # Using insecure random instead of secrets module
        chars = string.ascii_letters + string.digits
        return '\'''\''.join(random.choice(chars) for _ in range(32))
    
    def generate_password_reset_token(self):
        """Generate password reset token - predictable"""
        import time
        # Using time-based seed - predictable
        random.seed(int(time.time()))
        return str(random.randint(100000, 999999))
    
    def generate_api_key(self):
        """Generate API key - weak randomness"""
        return hashlib.md5(str(random.random()).encode()).hexdigest()
EOF'

# PR 13: Path Traversal Vulnerability
create_pr 13 "Add file management system" \
"Implements file upload, download, and management features" \
'cat > src/python/app/file_manager.py << '\''EOF'\''
import os
import shutil

class FileManager:
    def __init__(self):
        self.base_directory = "/var/app/uploads/"
    
    def get_file_path(self, filename):
        """Get file path - path traversal vulnerability"""
        # No validation against path traversal attacks
        return os.path.join(self.base_directory, filename)
    
    def read_file(self, filename):
        """Read file - vulnerable to path traversal"""
        file_path = self.get_file_path(filename)
        with open(file_path, '\''r'\'') as f:
            return f.read()
    
    def delete_file(self, filename):
        """Delete file - can be exploited for path traversal"""
        file_path = self.get_file_path(filename)
        os.remove(file_path)
        
    def copy_file(self, source_filename, dest_filename):
        """Copy file - both parameters vulnerable"""
        source = self.get_file_path(source_filename)
        dest = self.get_file_path(dest_filename)
        shutil.copy2(source, dest)
EOF'

# PR 14: Poor Exception Handling
create_pr 14 "Add data parsing utilities" \
"Implements parsers for various data formats" \
'cat > src/python/app/data_parser.py << '\''EOF'\''
import json
import xml.etree.ElementTree as ET

class DataParser:
    def parse_integer(self, value):
        """Parse integer - too broad exception handling"""
        try:
            return int(value)
        except Exception as e:  # Too broad - catches everything
            return 0
    
    def parse_json(self, json_string):
        """Parse JSON - generic exception thrown"""
        try:
            return json.loads(json_string)
        except:
            raise Exception("Failed to parse JSON")  # Generic exception
    
    def parse_xml(self, xml_string):
        """Parse XML - poor error handling"""
        try:
            return ET.fromstring(xml_string)
        except ET.ParseError:
            pass  # Silent failure
        except Exception as e:
            print(f"Error: {e}")  # Just printing, not proper error handling
            return None
EOF'

# PR 15: Memory Leaks and Inefficient Memory Usage
create_pr 15 "Add caching system" \
"Implements application-wide caching mechanism" \
'cat > src/python/app/cache_service.py << '\''EOF'\''
import threading

class CacheService:
    # Class-level cache - potential memory leak
    _cache = {}
    _lock = threading.Lock()
    
    @classmethod
    def put(cls, key, value):
        """Put value in cache - no expiration, grows indefinitely"""
        with cls._lock:
            cls._cache[key] = value
    
    @classmethod
    def get(cls, key):
        """Get value from cache"""
        with cls._lock:
            return cls._cache.get(key)
    
    @classmethod
    def put_with_metadata(cls, key, value, metadata):
        """Put with metadata - creates nested structures"""
        with cls._lock:
            if key not in cls._cache:
                cls._cache[key] = {}
            cls._cache[key]['\''data'\''] = value
            cls._cache[key]['\''metadata'\''] = metadata
            cls._cache[key]['\''access_count'\''] = cls._cache[key].get('\''access_count'\'', 0) + 1
EOF'

# PR 16: Inefficient String Operations
create_pr 16 "Add report generation system" \
"Generates various types of reports in different formats" \
'cat > src/python/app/report_generator.py << '\''EOF'\''
class ReportGenerator:
    def generate_csv_report(self, data_rows):
        """Generate CSV report - inefficient string concatenation"""
        csv_content = ""
        
        # Inefficient string concatenation in loop
        for row in data_rows:
            csv_content += ",".join(str(cell) for cell in row) + "\n"
        
        return csv_content
    
    def generate_html_report(self, data):
        """Generate HTML report - more inefficient concatenation"""
        html = "<html><body><table>"
        
        for item in data:
            html += "<tr>"
            html += f"<td>{item.get('\''name'\'', '\'''\'')}</td>"
            html += f"<td>{item.get('\''value'\'', '\'''\'')}</td>"
            html += f"<td>{item.get('\''date'\'', '\'''\'')}</td>"
            html += "</tr>"
        
        html += "</table></body></html>"
        return html
    
    def create_log_summary(self, log_entries):
        """Create log summary - quadratic time complexity"""
        summary = ""
        for i, entry in enumerate(log_entries):
            summary += f"Entry {i}: {entry}\n"
            # Inefficient nested loop
            for j in range(i):
                summary += f"  Related to entry {j}\n"
        return summary
EOF'

# PR 17: Deserialization and XML Vulnerabilities
create_pr 17 "Add XML processing capabilities" \
"Implements XML parsing and data processing from external sources" \
'cat > src/python/app/xml_processor.py << '\''EOF'\''
import xml.etree.ElementTree as ET
import pickle
import yaml

class XmlProcessor:
    def parse_xml_from_string(self, xml_content):
        """Parse XML - vulnerable to XXE attacks"""
        # No protection against XML External Entity attacks
        parser = ET.XMLParser()
        root = ET.fromstring(xml_content, parser)
        return root
    
    def deserialize_data(self, serialized_data):
        """Deserialize data - pickle vulnerability"""
        # Pickle can execute arbitrary code
        return pickle.loads(serialized_data)
    
    def load_yaml_config(self, yaml_content):
        """Load YAML configuration - unsafe loading"""
        # yaml.load is dangerous - can execute arbitrary Python code
        return yaml.load(yaml_content)
    
    def process_xml_file(self, file_path):
        """Process XML file - potential XXE via file"""
        parser = ET.XMLParser()
        tree = ET.parse(file_path, parser)
        return tree.getroot()
EOF'

# PR 18: Weak Cryptography and Hashing
create_pr 18 "Add security and encryption utilities" \
"Implements password hashing and data encryption" \
'cat > src/python/app/crypto_utils.py << '\''EOF'\''
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
        padded_data = data + '\'' '\'' * (8 - len(data) % 8)
        encrypted = cipher.encrypt(padded_data.encode())
        return base64.b64encode(encrypted).decode()
    
    def generate_simple_hash(self, text):
        """Generate simple hash - custom weak algorithm"""
        # Custom weak hashing algorithm
        result = 0
        for char in text:
            result = (result + ord(char)) * 37
        return str(result)
EOF'

# PR 19: Long Functions and Complex Logic
create_pr 19 "Add comprehensive user registration" \
"Implements complete user registration with validation and setup" \
'cat > src/python/app/user_registration.py << '\''EOF'\''
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
EOF'

# PR 20: Missing Input Validation
create_pr 20 "Add REST API endpoints" \
"Creates API endpoints for data processing and user management" \
'cat > src/python/app/api_controller.py << '\''EOF'\''
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

class ApiController:
    @app.route('\''/process_data'\'', methods=['\''POST'\''])
    def process_data(self):
        """Process data - no input validation"""
        data = request.json
        # No validation of input data
        result = data['\''input'\''].upper()  # Potential KeyError
        return jsonify({'\''result'\'': result})
    
    @app.route('\''/calculate'\'', methods=['\''POST'\''])
    def calculate(self):
        """Calculate values - no input validation"""
        data = request.json
        # No validation before conversion
        num1 = int(data['\''num1'\''])  # Potential ValueError/KeyError
        num2 = int(data['\''num2'\''])  # Potential ValueError/KeyError
        operation = data['\''operation'\'']  # No validation
        
        if operation == '\''add'\'':
            result = num1 + num2
        elif operation == '\''subtract'\'':
            result = num1 - num2
        else:
            result = 0
            
        return jsonify({'\''result'\'': result})
    
    @app.route('\''/execute_command'\'', methods=['\''POST'\''])
    def execute_command(self):
        """Execute system command - command injection vulnerability"""
        data = request.json
        command = data['\''command'\'']  # No validation - command injection risk
        # Dangerous: executing user input directly
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return jsonify({'\''output'\'': result.stdout, '\''error'\'': result.stderr})
EOF'

# PR 21-25: Good code examples
for i in {21..25}; do
    create_pr $i "Add utility functions (clean code)" \
    "Implements well-structured utility functions with proper error handling" \
    "cat > src/python/app/clean_utils_${i}.py << 'EOF'
\"\"\"
Clean, well-documented utility module
\"\"\"
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CleanUtils${i}:
    \"\"\"Well-structured utility class with proper error handling\"\"\"
    
    MAX_LIST_SIZE = 1000
    DEFAULT_ENCODING = 'utf-8'
    
    def process_string_list(self, items: Optional[List[str]]) -> List[str]:
        \"\"\"
        Process a list of strings with proper validation and error handling
        
        Args:
            items: List of strings to process, can be None
            
        Returns:
            List of processed strings (cleaned and capitalized)
            
        Raises:
            ValueError: If list is too large
        \"\"\"
        if items is None:
            logger.warning(\"Received None for items list\")
            return []
        
        if len(items) > self.MAX_LIST_SIZE:
            raise ValueError(f\"List size {len(items)} exceeds maximum {self.MAX_LIST_SIZE}\")
        
        result = []
        for item in items:
            if item and isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    result.append(cleaned.capitalize())
        
        logger.info(f\"Processed {len(result)} items from {len(items)} input items\")
        return result
    
    def safe_divide(self, dividend: float, divisor: float) -> Optional[float]:
        \"\"\"
        Safely divide two numbers with proper error handling
        
        Args:
            dividend: Number to be divided
            divisor: Number to divide by
            
        Returns:
            Result of division or None if invalid
        \"\"\"
        if not isinstance(dividend, (int, float)) or not isinstance(divisor, (int, float)):
            logger.error(\"Invalid input types for division\")
            return None
            
        if divisor == 0:
            logger.warning(\"Attempted division by zero\")
            return None
        
        return dividend / divisor
EOF"
done

# PR 26-30: Performance issues
for i in {26..30}; do
    create_pr $i "Add data processing (performance issues)" \
    "Implements data processing with performance concerns" \
    "cat > src/python/app/slow_processor_${i}.py << 'EOF'
class SlowProcessor${i}:
    def find_duplicates(self, data_list):
        \"\"\"Find duplicates - O(n^2) complexity\"\"\"
        duplicates = []
        
        # Inefficient nested loops - should use set or dict
        for i in range(len(data_list)):
            for j in range(i + 1, len(data_list)):
                if data_list[i] == data_list[j] and data_list[i] not in duplicates:
                    duplicates.append(data_list[i])
        
        return duplicates
    
    def inefficient_search(self, items, target):
        \"\"\"Inefficient linear search in sorted data\"\"\"
        # Should use binary search for sorted data
        for i, item in enumerate(items):
            if item == target:
                return i
        return -1
    
    def create_report(self, data):
        \"\"\"Generate report with string concatenation in loop\"\"\"
        report = \"\"
        for item in data:
            # Inefficient string concatenation
            report += f\"Item: {item['name']}, Value: {item['value']}\\n\"
        return report
EOF"
done

# PR 31-35: Security issues  
for i in {31..35}; do
    create_pr $i "Add authentication (security vulnerabilities)" \
    "Implements authentication with various security issues" \
    "cat > src/python/app/auth_${i}.py << 'EOF'
import hashlib
import jwt

class AuthService${i}:
    # Hardcoded secret key
    SECRET_KEY = \"hardcoded-jwt-secret-key-${i}\"
    
    def authenticate_user(self, username, password):
        \"\"\"Authenticate user - weak password hashing\"\"\"
        # Using weak MD5 hashing
        password_hash = hashlib.md5(password.encode()).hexdigest()
        
        # Hardcoded admin credentials
        if username == \"admin\" and password == \"admin123\":
            return True
        
        return self._check_password_in_db(username, password_hash)
    
    def generate_token(self, user_id):
        \"\"\"Generate JWT token - using hardcoded secret\"\"\"
        payload = {
            \"user_id\": user_id,
            \"role\": \"user\"
        }
        # Using hardcoded secret key
        return jwt.encode(payload, self.SECRET_KEY, algorithm=\"HS256\")
    
    def _check_password_in_db(self, username, password_hash):
        return False  # Stub
EOF"
done

# PR 36-40: Code quality issues
for i in {36..40}; do
    create_pr $i "Add helper class (code quality issues)" \
    "Implements helper class with various code quality problems" \
    "cat > src/python/app/helper_${i}.py << 'EOF'
class Helper${i}:
    def complex_condition_check(self, x, y, z, flag):
        \"\"\"Complex nested conditions - needs refactoring\"\"\"
        if x is not None:
            if x > 0:
                if y is not None:
                    if y < 100:
                        if z is not None:
                            if z > 10:
                                if flag:
                                    return \"success\"
                                else:
                                    return \"flag_false\"
                            else:
                                return \"z_too_small\"
                        else:
                            return \"z_is_none\"
                    else:
                        return \"y_too_large\"
                else:
                    return \"y_is_none\"
            else:
                return \"x_not_positive\"
        else:
            return \"x_is_none\"
    
    def do_multiple_things(self, data):
        \"\"\"Method doing too many things - violates SRP\"\"\"
        # Validate data
        if not data:
            return None
        
        # Process data
        processed = []
        for item in data:
            processed.append(item * 2)
        
        # Calculate stats
        total = sum(processed)
        average = total / len(processed)
        
        # Format output
        result = f\"Total: {total}, Average: {average:.2f}\"
        
        # Log result
        print(f\"Processed {len(data)} items: {result}\")
        
        return result
EOF"
done

# PR 41-45: Mixed issues
for i in {41..45}; do
    create_pr $i "Add service layer (mixed issues)" \
    "Implements service with various code quality and security issues" \
    "cat > src/python/app/service_${i}.py << 'EOF'
import sqlite3
import random

class Service${i}:
    def __init__(self):
        self.db_connection = \"sqlite:///app.db\"
        self.api_key = \"hardcoded-api-key-${i}\"
    
    def execute_query(self, user_input):
        \"\"\"Execute database query - SQL injection risk\"\"\"
        conn = sqlite3.connect(\"database.db\")
        cursor = conn.cursor()
        
        # SQL injection vulnerability
        query = f\"SELECT * FROM users WHERE name = '{user_input}'\"
        cursor.execute(query)
        
        results = cursor.fetchall()
        # Resource leak - connection not closed
        return results
    
    def generate_id(self):
        \"\"\"Generate ID - predictable random\"\"\"
        # Weak random number generation
        return random.randint(1000, 9999)
    
    def process_data(self, data):
        \"\"\"Process data - no error handling\"\"\"
        # No None check or error handling
        return data.upper().replace(\" \", \"_\")
EOF"
done

# PR 46-50: Minor issues (mostly good code with small problems)
for i in {46..50}; do
    create_pr $i "Add feature (minor code quality issues)" \
    "Implements feature with minor code quality issues" \
    "cat > src/python/app/feature_${i}.py << 'EOF'
class Feature${i}:
    def __init__(self):
        self.counter = 0
        self.items = []
    
    def add_item(self, item):
        \"\"\"Add item - minor: no input validation\"\"\"
        self.items.append(item)  # Could validate item is not None
        self.counter += 1
    
    def get_count(self):
        \"\"\"Get count\"\"\"
        return self.counter
    
    def get_items(self):
        \"\"\"Get items - minor: could return copy to prevent modification\"\"\"
        return self.items  # Should return copy for encapsulation
    
    def find_item(self, target):
        \"\"\"Find item - minor: could be more efficient\"\"\"
        # Linear search - fine for small lists, could use set for large ones
        for item in self.items:
            if item == target:
                return True
        return False
EOF"
done

# Summary
echo "================================================================================"
echo -e "${BLUE}🐍 PYTHON PR CREATION SUMMARY${NC}"
echo "================================================================================"
echo -e "✅ Successful:    ${GREEN}$SUCCESS_COUNT${NC}"
echo -e "❌ Failed:        ${RED}$FAILURE_COUNT${NC}"
echo "================================================================================"

if [ $FAILURE_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some PRs failed to create${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All Python PRs created successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "1. Review the created PRs at: ${YELLOW}https://github.com/${REPO_NAME}/pulls${NC}"
    echo -e "2. Update REPO_NAME variable in the script to match your repository"
    echo -e "3. Run your Python code analysis system on these PRs"
    exit 0
fi