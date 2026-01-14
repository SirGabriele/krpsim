from __future__ import annotations

import heapq
import logging
import random

from kr_config import MAX_WEIGHT, MAX_CYCLE_PER_MANAGER
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
                 resources: set[str],
                 end_timestamp: float,
                 weights: dict[str, float] | None = None
                 ):
        self.id = manager_id
        self.gen_id = gen_id
        self.processes = processes
        self.resources = resources
        self.stock = stock.clone()
        self.weights = self.__create_weights(weights)
        self.end_timestamp = end_timestamp
        self.processes_in_progress = []
        self.score = 0
        self.cycle = 0
        self.nb_completed_processes = 0
        self.print_trace = False
        self.__mutate()

    def __create_weights(self, weights: dict[str, float]) -> dict[str, float]:
        weights = (
            {resource: random.randint(0, MAX_WEIGHT) for resource in self.resources}
            if weights is None
            else weights.copy()
        )
        for resource_to_optimize in self.stock.resources_to_optimize:
            if not resource_to_optimize == "time":
                weights[resource_to_optimize] = MAX_WEIGHT * 1000000
        return weights

    def reset(self, stock: Stock, end_timestamp: float) -> None:
        """
        Resets the manager's state to erase its previous execution.
        :return: None
        """
        self.stock = stock.clone()
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
        logger.info("Running Generation [%d] - Manager [%d]", self.gen_id, self.id)
        logger.info(self.weights)
        while self.cycle < MAX_CYCLE_PER_MANAGER and not is_time_up(self.end_timestamp):
            completed_processes_count = self.__complete_processes()
            self.nb_completed_processes += completed_processes_count
            launched_processes = self.__launch_processes()

            if completed_processes_count == 0 and not launched_processes:
                if self.processes_in_progress:
                    self.cycle = self.__get_next_process_to_complete_remaining_duration()
                else:
                    logger.debug("Generation [%d] - Manager [%d] - No action can be done", self.gen_id - 1, self.id)
                    if self.print_trace:
                        print(f"No more process doable at time {self.cycle + 1}")
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

    def __score_process(self, process: Process) -> float:
        expenses = 0
        if process.inputs is not None:
            for input_resource, input_quantity in process.inputs.items():
                expenses += self.weights.get(input_resource, 0) * input_quantity
        income = 0
        if process.outputs is not None:
            for output_resource, output_quantity in process.outputs.items():
                income += self.weights.get(output_resource, 0) * output_quantity
        delay = process.delay if process.delay > 0 else 1
        return (income - expenses) / delay

    def __get_process_to_launch(self, launchable_processes: list[Process]) -> Process | None:
        """
        Selects the process to launch among the launchable ones.
        :return: Process
        """
        best_process = launchable_processes[0]
        best_score = self.__score_process(best_process)
        for process in launchable_processes[1:]:
            process_score = self.__score_process(process)
            if process_score > best_score:
                best_process = process
                best_score = process_score
        if best_score <= 0:
            return None
        return best_process

    def __launch_processes(self) -> list[Process]:
        """
        Launches a batch of processes.
        :return: None
        """
        launched_processes = []
        launchable_processes = self.__get_launchable_processes()


        while launchable_processes and not is_time_up(self.end_timestamp):
            process_to_launch = self.__get_process_to_launch(launchable_processes)
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
        logger.debug("Generation [{}] - Manager [{}] - Launch process '{}'".format(self.gen_id, self.id, process.name))
        if self.print_trace:
            print(f"{self.cycle}:{process.name}")

    def __evaluate(self) -> None:
        """
        Evaluates the manager's score for this generation.
        :return: None
        """
        for resource, quantity in self.stock.inventory.items():
            if resource not in self.stock.resources_to_optimize:
                self.score += self.weights.get(resource, 0) * quantity
        self.score += self.nb_completed_processes

    def __reverse_weights(self) -> None:
        active_keys = [k for k in self.weights if k not in self.stock.resources_to_optimize]
        sorted_keys = sorted(active_keys, key=self.weights.get)

        active_values = [self.weights[k] for k in active_keys]
        reversed_values = sorted(active_values, reverse=True)

        result = self.weights.copy()

        for key, new_value in zip(sorted_keys, reversed_values):
            result[key] = new_value
        self.weights = result

    def __mutate(self) -> None:
        """
        Performs mutation on the manager.
        :return: None
        """
        for resource in self.resources:
            if resource in self.stock.resources_to_optimize:
                continue
            if random.uniform(0, 1) >= 0.9:
                self.weights[resource] += random.uniform(-0.05 * MAX_WEIGHT, 0.05 * MAX_WEIGHT)
                self.weights[resource] = max(min(self.weights[resource], 0), MAX_WEIGHT)
            if random.uniform(0, 1) >= 0.95:
                self.weights[resource] += random.uniform(-0.2 * MAX_WEIGHT, 0.2 * MAX_WEIGHT)
                self.weights[resource] = max(min(self.weights[resource], 0), MAX_WEIGHT)
        if random.uniform(0, 1) >= 0.99:
            self.__reverse_weights()
