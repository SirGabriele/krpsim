from __future__ import annotations

import random
from copy import deepcopy
from typing import Optional

from process import Process
from stock import Stock

transposition_table: dict[str, Stock] = {}

class Manager:
    def __init__(self, stock: Stock,
                 processes: list[Process],
                 delay_max: int,
                 mother: Manager = None,
                 father: Manager = None,
                 ):
        self.processes = processes
        self.weights: dict[str, float] = {}
        if mother is None or father is None:
            self.aggressiveness_weight: float = random.random()
            for process in processes:
                self.weights[process.name] = random.random()
        else:
            self.reproduct(mother, father)
            self.mutate()

        self.stock = deepcopy(stock)
        self.delay_max = delay_max
        self.processes_in_progress: list[Process] = []
        self.score = 0
        self.actual_delay = 0
        self.processes_launched = {}
        self.processes_sorted = sorted(self.processes, key=lambda p: -self.weights.get(p.name, 0))
        self.deadlock = False

    def run(self):
        hash_weights = self.hash_weights()
        if hash_weights in transposition_table:
            self.stock = deepcopy(transposition_table[hash_weights])
        else:
            for i in range(self.delay_max):
                self.actual_delay += 1
                self.run_processes()
                if self.deadlock:
                    break
        transposition_table[hash_weights] = deepcopy(self.stock)
        self.evaluate()

    def launch_process(self, process: Process):
        can_launch = True
        for required_input, required_quantity in process.inputs.items():
            if self.stock.get_quantity(required_input) < required_quantity:
                can_launch = False
        if can_launch:
            self.processes_launched[process.name] = self.processes_launched.get(process.name, 0) + 1
            self.processes_in_progress.append(deepcopy(process))
            for required_input, required_quantity in process.inputs.items():
                self.stock.consume(required_input, required_quantity)

    def run_processes(self):
        lock = True
        for running_process in self.processes_in_progress:
            lock = False
            running_process.delay -= 1
            if running_process.delay <= 0:
                self.processes_in_progress.remove(running_process)
                for output, quantity in running_process.outputs.items():
                    self.stock.add(output, quantity)
        for process in self.processes_sorted:
            if self.weights.get(process.name, 0) > self.aggressiveness_weight:
                self.launch_process(process)
                lock = False
        self.deadlock = lock

    def evaluate(self):
        self.score = 0

    def reproduct(self, mother: Manager, father: Manager):
        for process in self.processes:
            weight_process_mother = mother.weights.get(process.name, 0)
            weight_process_father = father.weights.get(process.name, 0)
            self.weights[process.name] = random.choice([weight_process_mother, weight_process_father])
        weight_aggressiveness_father = father.aggressiveness_weight
        weight_aggressiveness_mother = mother.aggressiveness_weight
        self.aggressiveness_weight = random.choice([weight_aggressiveness_mother, weight_aggressiveness_father])

    def mutate(self):
        for process in self.processes:
            if random.uniform(0, 1) >= 0.25:
                self.weights[process.name] += random.uniform(-0.2, 0.2)
        if random.uniform(0, 1) >= 0.25:
            self.aggressiveness_weight += random.uniform(-0.2, 0.2)


    def hash_weights(self) -> str:
        hash = ""
        aggressiveness_included = False
        for process in self.processes_sorted:
            process_weight = self.weights.get(process.name, 0)
            if (not aggressiveness_included) and (process_weight < self.aggressiveness_weight):
                hash += f"AGGRESSIVE|"
                aggressiveness_included = True
            hash += f"{process.name}|"
        return hash
