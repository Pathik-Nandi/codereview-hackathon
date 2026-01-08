import threading

class CacheService:
    # Class-level cache - potential memory leak
    _cache = {}
    _lock = threading.Lock()
    
    @classmethod
    def put(cls, key, value):
        """Put value in cache - no expiration, grows indefinitely"""
        with cls._lock:
            cls._cache[key] = value
    
    @classmethod
    def get(cls, key):
        """Get value from cache"""
        with cls._lock:
            return cls._cache.get(key)
    
    @classmethod
    def put_with_metadata(cls, key, value, metadata):
        """Put with metadata - creates nested structures"""
        with cls._lock:
            if key not in cls._cache:
                cls._cache[key] = {}
            cls._cache[key]['data'] = value
            cls._cache[key]['metadata'] = metadata
            cls._cache[key]['access_count'] = cls._cache[key].get('access_count', 0) + 1
