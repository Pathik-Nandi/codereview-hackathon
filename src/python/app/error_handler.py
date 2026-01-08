import json
import requests

class ErrorHandler:
    def read_config_file(self, config_path):
        """Read configuration - empty exception handling"""
        try:
            with open(config_path, 'r') as f:
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
