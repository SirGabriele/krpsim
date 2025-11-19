import random
from copy import deepcopy

from process import Process
from stock import Stock


class Manager:
    def __init__(self, stock: Stock, processes: list[Process], delay_max: int, parent_weight: dict[str, float]=None, parent_aggressiveness_weight: float=None):
        if parent_weight is None:
            self.weights: dict[str, float] = {}
            for process in processes:
                self.weights[process.name] = random.random()
        else:
            self.weights = parent_weight #apply mutation
        if parent_aggressiveness_weight is None:
            self.aggressiveness_weight: float = random.random()
        else:
            self.aggressiveness_weight = parent_aggressiveness_weight #apply mutation
        print(self.weights)
        self.stock = stock
        self.processes = processes
        self.delay_max = delay_max
        self.processes_in_progress: list[Process] = []
        self.score = 0
        self.actual_delay = 0

    def run(self):
        process_sorted = sorted(self.processes, key=lambda p: -self.weights.get(p.name, 0))
        print([process.name for process in process_sorted])
        for i in range(self.delay_max):
            self.actual_delay += 1
            self.run_processes()

    def launch_process(self, process: Process):
        can_launch = True
        for required_input, required_quantity in process.inputs.items():
            if self.stock.get_quantity(required_input) < required_quantity:
                can_launch = False
        if can_launch:
            for required_input, required_quantity in process.inputs.items():
                print(f"{self.actual_delay}: {process.name}")
                self.processes_in_progress.append(deepcopy(process))
                self.stock.consume(required_input, required_quantity)

    def run_processes(self):
        for running_process in self.processes_in_progress:
            running_process.delay -= 1
            if running_process.delay <= 0:
                self.processes_in_progress.remove(running_process)
                for output, quantity in running_process.outputs.items():
                    self.stock.add(output, quantity)
        for process in self.processes:
            if self.weights.get(process.name, 0) > self.aggressiveness_weight:
                self.launch_process(process)