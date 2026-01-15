from __future__ import annotations

import heapq
import logging
import random
from uuid import uuid4

from kr_config import MAX_COMPLETED_PROCESSES_PER_MANAGER, MAX_CYCLE_PER_MANAGER, MUTATION_RATE
from process import Process
from stock import Stock
from utils.is_time_up import is_time_up


logger = logging.getLogger()

class Manager:
    def __init__(self,
                 manager_id: int,
                 gen_id: int,
                 stock: Stock,
                 processes: list[Process],
                 end_timestamp: float,
                 weights: dict[str, float] | None = None,
                 random_wait_uuid: str = None
                 ):
        self.id = manager_id
        self.gen_id = gen_id
        self.processes = processes
        self.random_wait_uuid = random_wait_uuid if random_wait_uuid is not None else str(uuid4())
        self.weights = (
            {process.name: random.random() for process in processes}
            if weights is None
            else weights
        )
        self.weights[self.random_wait_uuid] = random.random()
        self.random_seed = random.randint(0, 100000)
        self.rng_seed = random.Random(self.random_seed)
        self.stock = stock.clone()
        self.end_timestamp = end_timestamp
        self.processes_in_progress = []
        self.score = 0
        self.cycle = 0
        self.nb_completed_processes = 0
        self.print_trace = False
        self.__mutate()

    def reset(self, stock: Stock, end_timestamp: float) -> None:
        """
        Resets the manager's state to erase its previous execution.
        :return: None
        """
        self.stock = stock.clone()
        self.rng_seed = random.Random(self.random_seed)
        self.score = 0
        self.cycle = 0
        self.nb_completed_processes = 0
        self.processes_in_progress = []
        self.end_timestamp = end_timestamp

    def run(self, print_trace: bool = False) -> None:
        """
        Starts the manager's lifecycle. It lasts as long as it does not reach the maximum allowed actions or maximum allowed cycles
        and that time is not up.
        :return: None
        """
        self.print_trace = print_trace
        #print("Generation [{}] - Manager [{}]".format(self.gen_id, self.id))
        while ((self.nb_completed_processes < MAX_COMPLETED_PROCESSES_PER_MANAGER and self.cycle < MAX_CYCLE_PER_MANAGER)
               and not is_time_up(self.end_timestamp)):
            completed_processes_count = self.__complete_processes()
            self.nb_completed_processes += completed_processes_count
            launched_processes = self.__launch_processes()

            if completed_processes_count == 0 and not launched_processes:
                if self.processes_in_progress:
                    self.cycle = self.__get_next_process_to_complete_remaining_duration()
                else:
                    break
        self.__evaluate()

    def __get_next_process_to_complete_remaining_duration(self) -> int:
        """
        Gets the remaining duration until the next process completes.
        :return: int
        """
        return self.processes_in_progress[0][0]

    def __complete_processes(self) -> int:
        """
        Completes the execution of processes tge cycle duration of which is elapsed
        If the process has outputs, adds them to the stock.
        :return: int - The amount of completed processes.
        """
        completed_processes = 0
        while (self.processes_in_progress and self.__get_next_process_to_complete_remaining_duration() <= self.cycle
            and not is_time_up(self.end_timestamp)):
            _, _, process = heapq.heappop(self.processes_in_progress)
            if process.outputs is not None:
                for output, quantity in process.outputs.items():
                    self.stock.add(output, quantity)
            completed_processes += 1
        return completed_processes

    def __launch_processes(self) -> list[Process]:
        """
        Launches a batch of processes.
        :return: None
        """
        launched_processes = []
        launchable_processes = self.__get_launchable_processes()

        while launchable_processes and not is_time_up(self.end_timestamp):
            launchable_processes.append(None)
            # Creates a list containing all weights of each launchable process
            processes_weights = [self.weights.get(process.name, 0) if process is not None else self.weights[self.random_wait_uuid] for process in launchable_processes]
            # Selects the process to launch among the launchable ones
            process_to_launch = self.rng_seed.choices(population=launchable_processes, weights=processes_weights, k=1)[0]
            if process_to_launch is None:
                break
            self.__launch_process(process_to_launch)

            # Keeps track of launched processes
            launched_processes.append(process_to_launch)

            # Gets new list of launchable processes
            launchable_processes = self.__get_launchable_processes()
        return launched_processes

    def __get_launchable_processes(self) -> list[Process]:
        """
        Returns a list of processes that can be launched, aka processes the inputs of which are in stock.
        :return: list
        """
        return [process for process in self.processes if self.stock.can_launch_process(process)]

    def __launch_process(self, process: Process) -> None:
        """
        Launches a single process. Adds the process to the list of processes in progress.
        If the process has inputs, subtracts them from the stock.
        :return: None
        """
        heapq.heappush(self.processes_in_progress, (self.cycle + process.delay, id(process), process))
        if process.inputs is not None:
            for required_input, required_quantity in process.inputs.items():
                self.stock.consume(required_input, required_quantity)
        if self.print_trace:
            print(f"{self.cycle}:{process.name}")

    def __evaluate(self) -> None:
        """
        Evaluates the manager's score for this generation.
        :return: None
        """
        for resource in self.stock.resources_to_optimize:
            self.score += self.stock.get_quantity(resource) * 100000
        self.score -= self.nb_completed_processes
        self.score -= self.cycle

    def __mutate(self) -> None:
        for process in self.processes:
            if random.random() < MUTATION_RATE:
                delta = random.gauss(0, 0.1)
                self.weights[process.name] += delta
                self.weights[process.name] = max(min(1.0, self.weights[process.name]), 0.001)

        if random.random() < MUTATION_RATE:
            self.weights[self.random_wait_uuid] += random.gauss(0, 0.1)
            self.weights[self.random_wait_uuid] = max(min(1.0, self.weights[self.random_wait_uuid]), 0.001)
