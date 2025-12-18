from __future__ import annotations

import datetime
import heapq
import random
from copy import deepcopy

from process import Process
from stock import Stock

MAX_ACTION = 15000


def stock_output(outputs: dict[str, int]) -> int:
    quantity = 1
    if outputs is None:
        return quantity
    for output in outputs:
        quantity += outputs[output]
    return quantity


class Manager:
    def __init__(self, stock: Stock,
                 processes: list[Process],
                 end_timestamp: float,
                 mother: Manager = None,
                 father: Manager = None,
                 ):
        self.processes = processes
        self.weights: dict[str, float] = {}
        self.seed = random.Random(random.randint(0, 100000))
        if mother is None or father is None:
            for process in self.processes:
                self.weights[process.name] = random.random()
        else:
            self.reproduce(mother, father)
            self.mutate()

        self.stock = deepcopy(stock) #TODO methode clone sur stock
        self.end_timestamp = end_timestamp
        self.processes_in_progress = []
        self.score = 0
        self.cycle = 0
        self.action_done = 0

    def run(self):
        while self.action_done < MAX_ACTION:#and self.end_timestamp > datetime.datetime.now().timestamp():
            nb_finished = self.update_action()
            self.action_done += nb_finished
            launched_list = self.choose_action()
            if nb_finished == 0 and not launched_list:
                if self.processes_in_progress:
                    self.cycle = self.processes_in_progress[0][0]
                else:
                    break
        self.evaluate()

    def update_action(self) -> int:
        action_done = 0
        while self.processes_in_progress and self.processes_in_progress[0][0] <= self.cycle:
            time, _, process = heapq.heappop(self.processes_in_progress)
            for output, quantity in process.outputs.items():
                self.stock.add(output, quantity)
            action_done += 1
        return action_done

    def choose_action(self):
        chosen_process = []
        processes_available = self.get_processes_available()
        while processes_available:
            processes_weights = []
            for process in processes_available:
                processes_weights.append(self.weights.get(process.name, 0))
            if sum(processes_weights) <= 0:
                processes_weights = [1] * len(processes_weights)
            chosen_process.append(self.seed.choices(processes_available, processes_weights, k=1)[0])
            self.process_launch(chosen_process[-1])
            processes_available = self.get_processes_available()
        return chosen_process

    def get_processes_available(self):
        processes_available = []
        for process in self.processes:
            if self.process_can_launch(process):
                processes_available.append(process)
        return processes_available

    def process_can_launch(self, process: Process):
        for required_input, required_quantity in process.inputs.items():
            if self.stock.get_quantity(required_input) < required_quantity:
                return False
        return True

    def process_launch(self, process: Process):
        heapq.heappush(self.processes_in_progress, (self.cycle + process.delay, id(process), process))
        for required_input, required_quantity in process.inputs.items():
            self.stock.consume(required_input, required_quantity)

    def evaluate(self):
        for resource in self.stock.resources_to_optimize:
            self.score += self.stock.get_quantity(resource) * 1000
        self.score += self.action_done

    def reproduce(self, mother: Manager, father: Manager):
        for process in self.processes:
            weight_process_mother = mother.weights.get(process.name, 0)
            weight_process_father = father.weights.get(process.name, 0)
            self.weights[process.name] = random.choice([weight_process_mother, weight_process_father])

    def mutate(self):
        for process in self.processes:
            if random.uniform(0, 1) >= 0.25:
                self.weights[process.name] += random.uniform(-0.05, 0.05)
                self.weights[process.name] = max(min(1.0, self.weights[process.name]), 0)
