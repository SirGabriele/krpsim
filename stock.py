from dataclasses import dataclass, field
from typing import Dict

from process import Process


@dataclass
class Stock:
    inventory: Dict[str, int] = field(default_factory=dict, init=False)
    resources_to_optimize: list[str] = field(default_factory=list, init=False)

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

    def can_launch_process(self, process: Process) -> bool:
        if process.inputs is None:
            return False

        # This process does not require any input
        if not process.inputs:
            return True

        for input_name, input_amount in process.inputs.items():
            if input_name not in self.inventory or self.inventory[input_name] < input_amount:
                return False
        return True

    def __str__(self) -> str:
        return f"Stock: stock={self.inventory}"
