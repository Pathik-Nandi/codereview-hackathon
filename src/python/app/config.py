import os

class Config:
    """Configuration class with hardcoded secrets - security issue"""
    
    # Hardcoded database credentials
    DATABASE_URL = "postgresql://admin:SuperSecret123@localhost:5432/myapp"
    
    # Hardcoded API keys
    AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
    AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    
    # Social media API keys
    TWITTER_API_KEY = "xvz1evFS4wEEPTGEFPHBog"
    TWITTER_SECRET = "L8qq9PZyRg6ieKGEKhZolGC0vJWLw8iEJ88DRdyOg"
    
    # Payment gateway
    STRIPE_SECRET_KEY = "sk_test_26PHem9AhJZvU623DfE1x4sd"
    
    def get_db_connection(self):
        return self.DATABASE_URL
