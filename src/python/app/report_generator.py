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
            html += f"<td>{item.get('name', '')}</td>"
            html += f"<td>{item.get('value', '')}</td>"
            html += f"<td>{item.get('date', '')}</td>"
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
