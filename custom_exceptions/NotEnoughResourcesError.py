class NotEnoughResourcesError(Exception):

    def __init__(self, process_name: str, actual_stock: dict[str, int], required_ingredients: dict[str, int]):
        error_message = f"Not enough resources to run process '{process_name}'.\n"
        for ingredient, required_amount in required_ingredients.items():
            available_amount = actual_stock.get(ingredient, 0)
            if available_amount < required_amount:
                error_message += f"- Required: {required_amount} of '{ingredient}', Available: {available_amount}\n"
        self.message = error_message
        super().__init__(self.message)

    def __str__(self):
        return f"NotEnoughResourcesError: {self.message}"
