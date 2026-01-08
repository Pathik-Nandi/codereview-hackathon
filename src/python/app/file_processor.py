import json
import csv

class FileProcessor:
    def process_json_file(self, file_path):
        """Process JSON file - resource leak, file not closed properly"""
        file = open(file_path, 'r')
        data = json.load(file)
        # File not closed - resource leak
        
        return len(data) if data else 0
    
    def read_csv_file(self, file_path):
        """Read CSV file - another resource leak"""
        file = open(file_path, 'r')
        reader = csv.reader(file)
        rows = list(reader)
        # File handle not closed
        
        return rows
    
    def write_log(self, message, log_file="app.log"):
        """Write to log - resource not properly managed"""
        log = open(log_file, 'a')
        log.write(f"{message}\n")
        # Log file not closed
