from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Stock:
    inventory: Dict[str, int] = field(default_factory=dict)

    def add(self, resource: str, quantity: int) -> None:
        self.inventory[resource] = self.inventory.get(resource, 0) + quantity

    def consume(self, resource: str, quantity: int) -> bool:
        if resource in self.inventory and self.inventory[resource] >= quantity:
            self.inventory[resource] -= quantity
            return True
        return False

    def get_quantity(self, resource: str) -> int:
        return self.inventory.get(resource, 0)

    def get_total_quantity(self) -> int:
        return sum(self.inventory.values())

    def get_num_resources(self) -> int:
        return len(self.inventory)

    def __str__(self) -> str:
        return f"Stock: stock={self.inventory}"
