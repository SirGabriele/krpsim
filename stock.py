from dataclasses import dataclass, field

from process import Process


@dataclass
class Stock:
    inventory: dict[str, int] = field(default_factory=dict, init=False)
    resources_to_optimize: set[str] = field(default_factory=set, init=False)

    def clone(self) -> "Stock":
        new = Stock()
        new.inventory = self.inventory.copy()
        new.resources_to_optimize = self.resources_to_optimize.copy()
        return new

    def add(self, resource: str, quantity: int) -> None:
        self.inventory[resource] = self.inventory.get(resource, 0) + quantity

    def consume(self, resource: str, quantity: int) -> bool:
        if resource in self.inventory and self.inventory[resource] >= quantity:
            self.inventory[resource] -= quantity
            # Deletes the entry if quantity falls down to 0
            if self.inventory[resource] == 0:
                del self.inventory[resource]
            return True
        return False

    def get_quantity(self, resource: str) -> int:
        return self.inventory.get(resource, 0)

    def get_total_quantity(self) -> int:
        return sum(self.inventory.values())

    def can_launch_process(self, process: Process) -> bool:
        if process.inputs is None:
            return False

        # This process does not require any input
        if not process.inputs:
            return True

        if process.inputs is None:
            return False

        for input_name, input_amount in process.inputs.items():
            if input_name not in self.inventory or self.inventory[input_name] < input_amount:
                return False
        return True

    def __str__(self) -> str:
        return f"Stock: inventory={self.inventory}, resources_to_optimize={self.resources_to_optimize}"
