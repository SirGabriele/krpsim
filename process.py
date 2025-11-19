from typing import Dict

class Process:
    name: str
    inputs: Dict[str, int]
    outputs: Dict[str, int]
    delay: int
    in_progress: bool

    def __init__(self, name, inputs, outputs, delay):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.delay = delay
        self.in_progress = False

    def __str__(self) -> str:
        return f"Process(name={self.name}, inputs={self.inputs}, outputs={self.outputs}, delay={self.delay})"