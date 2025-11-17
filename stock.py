from typing import Dict

class Stock:
    stock: Dict[str, int]

    def __init__(self):
        self.stock = {}

    def add(self, resource: str, quantity: int):
        if resource in self.stock:
            self.stock[resource] += quantity
        else:
            self.stock[resource] = quantity

    def consume(self, resource: str, quantity: int) -> bool:
        if resource in self.stock and self.stock[resource] >= quantity:
            self.stock[resource] -= quantity
            return True
        return False

    def get_quantity(self, resource: str) -> int:
        return self.stock.get(resource, 0)

    def __str__(self) -> str:
        return str(self.stock)
