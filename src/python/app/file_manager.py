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
        with open(file_path, 'r') as f:
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
