from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

class ApiController:
    @app.route('/process_data', methods=['POST'])
    def process_data(self):
        """Process data - no input validation"""
        data = request.json
        # No validation of input data
        result = data['input'].upper()  # Potential KeyError
        return jsonify({'result': result})
    
    @app.route('/calculate', methods=['POST'])
    def calculate(self):
        """Calculate values - no input validation"""
        data = request.json
        # No validation before conversion
        num1 = int(data['num1'])  # Potential ValueError/KeyError
        num2 = int(data['num2'])  # Potential ValueError/KeyError
        operation = data['operation']  # No validation
        
        if operation == 'add':
            result = num1 + num2
        elif operation == 'subtract':
            result = num1 - num2
        else:
            result = 0
            
        return jsonify({'result': result})
    
    @app.route('/execute_command', methods=['POST'])
    def execute_command(self):
        """Execute system command - command injection vulnerability"""
        data = request.json
        command = data['command']  # No validation - command injection risk
        # Dangerous: executing user input directly
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return jsonify({'output': result.stdout, 'error': result.stderr})
