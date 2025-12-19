from __future__ import annotations

import heapq
import logging
import random

from process import Process
from stock import Stock
from utils.is_time_up import is_time_up


MAX_ACTION = 15000

logger = logging.getLogger()

class Manager:
    def __init__(self,
                 manager_id: int,
                 gen_id: int,
                 stock: Stock,
                 processes: list[Process],
                 end_timestamp: float,
                 weights: dict[str, float] | None = None
                 ):
        self.id = manager_id
        self.gen_id = gen_id
        self.processes = processes
        self.weights = (
            {process.name: random.random() for process in processes}
            if weights is None
            else weights
        )
        self.random_seed = random.randint(0, 100000)
        self.rng_seed = random.Random(self.random_seed)
        self.stock = stock.clone()
        self.end_timestamp = end_timestamp
        self.processes_in_progress = []
        self.score = 0
        self.cycle = 0
        self.action_done = 0
        self.print_trace = False
        self.mutate()

    def reset(self, stock: Stock):
        self.stock = stock.clone()
        self.rng_seed = random.Random(self.random_seed)
        self.score = 0
        self.cycle = 0
        self.action_done = 0
        self.processes_in_progress = []

    def run(self, print_trace: bool = False):
        self.print_trace = print_trace

        while self.action_done < MAX_ACTION and (not is_time_up(self.end_timestamp) or print_trace):
            completed_processes_count = self.complete_processes()
            self.action_done += completed_processes_count
            launch_processes = self.launch_processes()

            if completed_processes_count == 0 and not launch_processes:
                if self.processes_in_progress:
                    self.cycle = self.get_next_process_to_complete_time()
                else:
                    logger.debug("Generation [%d] - Manager [%d] - No action can be done", self.gen_id, self.id)
                    break
        self.evaluate()

    def get_next_process_to_complete_time(self):
        return self.processes_in_progress[0][0]

    def complete_processes(self) -> int:
        completed_processes = 0
        while self.processes_in_progress and self.get_next_process_to_complete_time() <= self.cycle:
            _, _, process = heapq.heappop(self.processes_in_progress)
            if process.outputs is not None:
                for output, quantity in process.outputs.items():
                    self.stock.add(output, quantity)
            completed_processes += 1
        return completed_processes

    def launch_processes(self):
        launched_processes = []
        launchable_processes = self.get_launchable_processes()

        while launchable_processes:
            # Creates a list containing all weights of each launchable process
            processes_weights = [self.weights.get(process.name, 0) for process in launchable_processes]

            # Selects the process to launch among the launchable ones
            process_to_launch = self.rng_seed.choices(population=launchable_processes, weights=processes_weights, k=1)[0]
            self.process_launch(process_to_launch)

            # Keeps track of launched processes
            launched_processes.append(process_to_launch)

            # Gets new list of launchable processes
            launchable_processes = self.get_launchable_processes()
        return launched_processes

    def get_launchable_processes(self):
        return [process for process in self.processes if self.stock.can_launch_process(process)]

    def process_launch(self, process: Process):
        heapq.heappush(self.processes_in_progress, (self.cycle + process.delay, id(process), process))
        if process.inputs is not None:
            for required_input, required_quantity in process.inputs.items():
                self.stock.consume(required_input, required_quantity)
        logger.debug("Generation [{}] - Manager [{}] - Launch process '{}'".format(self.gen_id, self.id, process.name))
        if self.print_trace:
            print(f"{self.cycle}:{process.name}")

    def evaluate(self):
        for resource in self.stock.resources_to_optimize:
            self.score += self.stock.get_quantity(resource) * 100000
        self.score += self.action_done

    def mutate(self):
        for process in self.processes:
            if random.uniform(0, 1) >= 0.75:
                self.weights[process.name] += random.uniform(-0.05, 0.05)
                self.weights[process.name] = max(min(1.0, self.weights[process.name]), 0.001)
