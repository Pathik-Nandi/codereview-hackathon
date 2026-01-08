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
        return re.findall(rd+, text)  # TypeError if text is None
    
    def process_list(self, items):
        """Process list - no None or empty checks"""
        return [item.upper() for item in items]  # Multiple potential errors
    
    def get_dict_value(self, data, key):
        """Get dictionary value - no validation"""
        return data[key].strip()  # Multiple potential errors
