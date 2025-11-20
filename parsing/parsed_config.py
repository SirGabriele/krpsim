from dataclasses import dataclass

from process import Process
from stock import Stock


@dataclass
class ParsedConfig:
    stock: Stock
    processes: list[Process]
    to_optimize: list[str]

    def __str__(self) -> str:
        return (
            f"Stock: {self.stock}\n"
            f"Processes: {self.processes}\n"
            f"to_optimize: {self.to_optimize}"
        )