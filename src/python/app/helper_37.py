class Helper37:
    def complex_condition_check(self, x, y, z, flag):
        """Complex nested conditions - needs refactoring"""
        if x is not None:
            if x > 0:
                if y is not None:
                    if y < 100:
                        if z is not None:
                            if z > 10:
                                if flag:
                                    return "success"
                                else:
                                    return "flag_false"
                            else:
                                return "z_too_small"
                        else:
                            return "z_is_none"
                    else:
                        return "y_too_large"
                else:
                    return "y_is_none"
            else:
                return "x_not_positive"
        else:
            return "x_is_none"
    
    def do_multiple_things(self, data):
        """Method doing too many things - violates SRP"""
        # Validate data
        if not data:
            return None
        
        # Process data
        processed = []
        for item in data:
            processed.append(item * 2)
        
        # Calculate stats
        total = sum(processed)
        average = total / len(processed)
        
        # Format output
        result = f"Total: {total}, Average: {average:.2f}"
        
        # Log result
        print(f"Processed {len(data)} items: {result}")
        
        return result
