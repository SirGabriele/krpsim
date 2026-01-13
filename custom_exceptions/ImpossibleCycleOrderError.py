class ImpossibleCycleOrderError(Exception):

    def __init__(self, cycle: int, last_cycle:int, line_number: int):
        self.message = (
            f"Cycle {cycle} at line {line_number} is impossible after cycle {last_cycle}."
        )
        super().__init__(self.message)

    def __str__(self):
        return f"ImpossibleCycleOrderError: {self.message}"
