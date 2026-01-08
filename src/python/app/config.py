import os

class Config:
    """Configuration class with hardcoded secrets - security issue"""
    
    # Hardcoded database credentials
    DATABASE_URL = "postgresql://admin:SuperSecret123@localhost:5432/myapp"
    
    # Hardcoded API keys
    AWS_ACCESS_KEY = "FAKE_AWS_ACCESS_KEY_EXAMPLE"
    AWS_SECRET_KEY = "fake-aws-secret-key-for-testing-only"
    
    # Social media API keys
    TWITTER_API_KEY = "fake_twitter_api_key_example"
    TWITTER_SECRET = "fake_twitter_secret_for_testing"
    
    # Payment gateway
    STRIPE_SECRET_KEY = "fake_stripe_secret_key_for_testing"
    
    def get_db_connection(self):
        return self.DATABASE_URL
