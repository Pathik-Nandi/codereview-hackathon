class SlowProcessor29:
    def find_duplicates(self, data_list):
        """Find duplicates - O(n^2) complexity"""
        duplicates = []
        
        # Inefficient nested loops - should use set or dict
        for i in range(len(data_list)):
            for j in range(i + 1, len(data_list)):
                if data_list[i] == data_list[j] and data_list[i] not in duplicates:
                    duplicates.append(data_list[i])
        
        return duplicates
    
    def inefficient_search(self, items, target):
        """Inefficient linear search in sorted data"""
        # Should use binary search for sorted data
        for i, item in enumerate(items):
            if item == target:
                return i
        return -1
    
    def create_report(self, data):
        """Generate report with string concatenation in loop"""
        report = ""
        for item in data:
            # Inefficient string concatenation
            report += f"Item: {item['name']}, Value: {item['value']}\n"
        return report
