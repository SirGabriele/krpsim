import copy
import logging
import random

from process import Process
from stock import Stock
from utils.pluralize import pluralize


MAX_PROCESS_PER_GENERATION = 15000
POPULATION_SIZE = 1
MUTATION_RATE = 0.01

logger = logging.getLogger(__name__)


class Individual:
    def __init__(self, stock: Stock, processes: dict[str, Process], individual_id: int) -> None:
        self.id = individual_id
        self.stock: Stock = copy.deepcopy(stock)
        self.process_waiting_queue: list[Process] = []
        self.processes_in_progress: list[Process] = []
        self.weights: dict[str, float] = normalize_weights(
            {name: random.random() for name in processes.keys()})
        self.score: int = 0
        self.finished_processes: int = 0
        self.trace = ""

    def __str__(self) -> str:
        return (
            f"Individual: id={self.id}, stock={self.stock}, process_waiting_queue={self.process_waiting_queue}, "
            f"processes_in_progress={self.processes_in_progress}, weights={self.weights}, score={self.score}, "
            f"finished_processes={self.finished_processes}, trace={self.trace}"
        )


def normalize_weights(weights: dict[str, float]):
    total = sum(weights.values())
    if total == 0:
        raise ValueError("Can not normalize weights: sum is zero")
    return {k: v / total for k, v in weights.items()}


def generate_individual(initial_stock: Stock, processes: dict[str, Process],
                        individual_id: int) -> Individual:
    return Individual(stock=initial_stock, processes=processes, individual_id=individual_id)


def generate_population(size: int, initial_stock: Stock, processes: dict[str, Process]) -> list[Individual]:
    return [generate_individual(initial_stock, processes, index + 1) for index in range(size)]


def fitness(individual: Individual) -> None:
    score = 0
    for resource in individual.stock.resources_to_optimize:
        score += individual.stock.get_quantity(resource) * 100
    individual.score += score


def launch_process(stock: Stock, process: Process) -> None:
    for resource, quantity in process.inputs.items():
        stock.consume(resource, quantity)

    for resource, quantity in process.outputs.items():
        stock.add(resource, quantity)


def get_launchable_processes(stock: Stock, processes: dict[str, Process]) -> dict[str, Process]:
    return {
        process_name: process
        for process_name, process in processes.items()
        if stock.can_launch_process(process)
    }


def get_sum_weights(weights: dict[str, float], processes: dict[str, Process]) -> float:
    return sum(weights[process_name] for process_name in processes.keys())


def run_simulation(initial_stock: Stock, processes: dict[str, Process], delay_max: int) -> None:
    population = generate_population(size=POPULATION_SIZE, initial_stock=initial_stock, processes=processes)

    for generation_index, individual in enumerate(population):
        has_reached_max_processes = False
        has_ran_out_of_processes = False
        current_process_cycle = 0

        while not has_reached_max_processes and not has_ran_out_of_processes:
            launchable_processes = get_launchable_processes(stock=individual.stock, processes=processes)

            has_reached_max_processes = individual.finished_processes >= MAX_PROCESS_PER_GENERATION
            has_ran_out_of_processes = not launchable_processes and not individual.process_waiting_queue

            if not launchable_processes:
                len_process_waiting_queue = len(individual.process_waiting_queue)
                logger.debug(
                    "Individual [%d] - Not enough stock to launch any process. Process waiting queue contains %d %s",
                    individual.id,
                    len_process_waiting_queue,
                    pluralize("process", "es", len_process_waiting_queue)
                )

                while individual.process_waiting_queue:
                    process_to_finish = individual.process_waiting_queue.pop(0)

                    logger.debug("Individual [{}] - Launch process '{}'".format(individual.id, process_to_finish.name))
                    individual.trace += "{}: {}\n".format(current_process_cycle, process_to_finish.name)
                    current_process_cycle = max(current_process_cycle, process_to_finish.cycle_amount)

                    for resource, quantity in process_to_finish.outputs.items():
                        individual.stock.add(resource, quantity)
                    individual.finished_processes += 1
                continue

            sum_weights = get_sum_weights(weights=individual.weights, processes=launchable_processes)

            target_process_weight = random.uniform(0, sum_weights)
            weight_acc = 0

            for process_name, process in launchable_processes.items():
                weight_acc += individual.weights[process_name]
                if target_process_weight <= weight_acc:
                    individual.process_waiting_queue.append(process)

                    for resource, quantity in process.inputs.items():
                        individual.stock.consume(resource, quantity)
                    break

        individual.trace += "Final stock : {}".format(individual.stock.inventory)
        logger.debug("Generation [{}] - Individual [{}] - Final stock : {}".format(generation_index + 1, individual.id, individual.stock))
        print(individual.trace)
