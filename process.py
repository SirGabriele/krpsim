from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Process:
    name: str
    inputs: Dict[str, int] | None
    outputs: Dict[str, int] | None
    cycle_amount: int

    def __str__(self) -> str:
        return (f"Process: name={self.name}\n"
                f"\tinputs={self.inputs}\n"
                f"\toutputs={self.outputs}\n"
                f"\tcycle_amount={self.cycle_amount}")
