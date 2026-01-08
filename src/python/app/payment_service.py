import hashlib
import hmac

class PaymentService:
    def process_credit_card(self, card_number, amount, cvv):
        """Process credit card payment - duplicated validation logic"""
        if not card_number or len(card_number.replace(" ", "")) != 16:
            print("Invalid card number")
            return False
        
        if not amount or amount <= 0:
            print("Invalid amount")
            return False
            
        if not cvv or len(cvv) != 3:
            print("Invalid CVV")
            return False
            
        print("Processing credit card payment...")
        return self._charge_card(card_number, amount)
    
    def process_debit_card(self, card_number, amount, pin):
        """Process debit card payment - same validation duplicated"""
        if not card_number or len(card_number.replace(" ", "")) != 16:
            print("Invalid card number")
            return False
        
        if not amount or amount <= 0:
            print("Invalid amount")
            return False
            
        if not pin or len(pin) != 4:
            print("Invalid PIN")
            return False
            
        print("Processing debit card payment...")
        return self._charge_card(card_number, amount)
    
    def _charge_card(self, card_number, amount):
        return True  # Simulated success
