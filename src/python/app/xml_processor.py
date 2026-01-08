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
