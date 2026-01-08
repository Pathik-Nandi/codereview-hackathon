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
            'total_requests': self.count,
            'avg_requests_per_minute': len(self.request_times) / 60 if self.request_times else 0
        }
