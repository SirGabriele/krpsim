from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Stock:
    inventory: Dict[str, int] = field(default_factory=dict)

    def add(self, resource: str, quantity: int) -> None:
        if resource in self.inventory:
            self.inventory[resource] += quantity
        else:
            self.inventory[resource] = quantity

    def consume(self, resource: str, quantity: int) -> bool:
        if resource in self.inventory and self.inventory[resource] >= quantity:
            self.inventory[resource] -= quantity
            return True
        return False

    def get_quantity(self, resource: str) -> int:
        return self.inventory.get(resource, 0)

    def __str__(self) -> str:
        return f"Stock: stock={self.inventory}"
