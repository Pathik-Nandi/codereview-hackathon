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
