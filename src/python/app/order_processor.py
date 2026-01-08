class OrderProcessor:
    def process_order(self, order):
        """Process order with high cyclomatic complexity - needs refactoring"""
        if order is not None:
            if order.get('amount') is not None and order['amount'] > 0:
                if order.get('customer') is not None:
                    customer = order['customer']
                    if customer.get('verified') is True:
                        if order.get('items') is not None and len(order['items']) > 0:
                            for item in order['items']:
                                if item.get('quantity') is not None and item['quantity'] > 0:
                                    if item.get('price') is not None and item['price'] > 0:
                                        if item.get('available') is True:
                                            if order.get('shipping_address') is not None:
                                                if order.get('payment_method') is not None:
                                                    payment = order['payment_method']
                                                    if payment.get('type') in ['credit_card', 'debit_card', 'paypal']:
                                                        if payment.get('validated') is True:
                                                            return self._execute_order(order)
        return False
    
    def _execute_order(self, order):
        return True
