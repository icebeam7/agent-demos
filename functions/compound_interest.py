import json

class CompoundInterest:
    def calculate_future_value(current_price: float, 
                               monthly_interest_rate: float = 0.02, 
                               months: int = 12) -> str:
        """
        Calculates the future value of an item after N months given the current value and a monthly interest rate.

        :param current_price: Current price of the item.
        :param monthly_interest_rate: Monthly interest rate. Default is 0.02 (2%) if not provided.
        :param months: Number of months in the future. Default is 12 months if not provided.
        :return: Future value of the item.
        """
        future_value = current_price * ((1 + monthly_interest_rate) ** months)
        print(f"Future value calculated: {future_value} for current price: {current_price}")
        return json.dumps({"future_value": future_value})
