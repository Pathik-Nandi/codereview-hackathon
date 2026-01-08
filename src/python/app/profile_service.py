class ProfileService:
    def get_user_email(self, user):
        """Get user email - potential AttributeError if user is None"""
        return user.email.lower()  # No None check
    
    def get_full_name(self, user):
        """Get full name - multiple None reference risks"""
        return f"{user.first_name} {user.last_name}"  # No None checks
    
    def get_user_age(self, user):
        """Calculate age - potential errors"""
        from datetime import date
        return (date.today() - user.birth_date).days // 365
    
    def format_address(self, user):
        """Format address - chain of potential None references"""
        return f"{user.address.street}, {user.address.city}, {user.address.country}"
