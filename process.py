from dataclasses import dataclass, field


@dataclass
class Process:
    name: str
    inputs: dict[str, int] | None
    outputs: dict[str, int] | None
    delay: int
    in_progress: bool = field(default=False)

    def __str__(self) -> str:
        return f"Process: name={self.name}, inputs={self.inputs}, outputs={self.outputs}, delay={self.delay}"
