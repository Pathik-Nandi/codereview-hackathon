import re

class Validator:
    def validate_age(self, age):
        """Validate age - magic numbers without constants"""
        return 18 <= age <= 120  # Magic numbers
    
    def validate_password(self, password):
        """Validate password - hardcoded rules"""
        if not password or len(password) < 8:  # Magic number
            return False
        if len(password) > 64:  # Magic number
            return False
        return True
    
    def validate_phone(self, phone):
        """Validate phone number - magic pattern"""
        if not phone or len(phone) != 10:  # Magic number
            return False
        return phone.isdigit()
    
    def validate_credit_card(self, card_number):
        """Validate credit card - magic numbers"""
        if not card_number:
            return False
        # Remove spaces and dashes
        clean_number = re.sub(r"[\s-]", "", card_number)
        return len(clean_number) == 16 and clean_number.isdigit()  # Magic number
