from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Process:
    name: str
    inputs: Dict[str, int] | None
    outputs: Dict[str, int] | None
    delay: int

    def __str__(self) -> str:
        return f"Process: name={self.name}, inputs={self.inputs}, outputs={self.outputs}, delay={self.delay}"
