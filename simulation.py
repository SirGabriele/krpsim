import logging
import random
import time

from kr_config import POPULATION_SIZE
from process import Process
from stock import Stock
from Manager import Manager
from utils.is_time_up import is_time_up


logger = logging.getLogger()

def get_top_five_percent() -> int:
    """
    Calculates the amount of individuals that equals five percent of the population.
    :return: int
    """
    return int(POPULATION_SIZE * 5 / 100)

def next_generation(gen_id: int, sorted_population: list[Manager], stock: Stock, processes: list[Process], resources: set[str], delay_max: float) -> list[Manager]:
    """
    Creates the next generation. Keeps the top five percent of the current population and moves them into the next one.
    For the remaining ninety-five percent, picks two random individuals and "breed" them to obtain a new individual.
    This "breeding" is performed using a uniform crossover to determine the new individual's processes' weights.
    :return: list[Manager]
    """
    top_five_percent = get_top_five_percent()
    remaining_managers_to_generate = POPULATION_SIZE - top_five_percent
    managers_score = [manager.score for manager in sorted_population]
    new_population = sorted_population[:top_five_percent]
    end_timestamp = time.monotonic() + delay_max

    for i in range(remaining_managers_to_generate):
        # Selects two random distinct managers to breed
        parent_one, parent_two = random.choices(sorted_population, weights=managers_score, k=2)
        while parent_two == parent_one:
            parent_two = random.choices(sorted_population, weights=managers_score, k=1)[0]

        weights: dict[str, float] = {}
        for resource in resources:
            # Uniform crossover. Each weight has a 50% chance to be from parent one and a 50% chance to be from parent two
            weights[resource] = parent_one.weights[resource] if random.random() < 0.5 else parent_two.weights[resource]

        new_population.append(generate_individual(manager_id=i + 1, gen_id=gen_id, stock=stock, processes=processes, resources=resources, end_timestamp=end_timestamp, weights=weights))

    return new_population

def generate_individual(gen_id: int, stock: Stock, processes: list[Process], resources: set[str], manager_id: int, end_timestamp: float, weights: dict[str, float] | None = None) -> Manager:
    """
    Generates one individual.
    :return: Manager
    """
    return Manager(manager_id=manager_id, gen_id=gen_id, stock=stock, processes=processes, resources=resources, end_timestamp=end_timestamp, weights=weights)

def get_all_resources(processes: list[Process]) -> set[str]:
    """
    Returns a set of all resources involved in the processes.
    :return: set[str]
    """
    resources: set[str] = set()
    for process in processes:
        if process.inputs is not None:
            for input_resource in process.inputs.keys():
                resources.add(input_resource)
        if process.outputs is not None:
            for output_resource in process.outputs.keys():
                resources.add(output_resource)
    return resources

def generate_population(size: int, gen_id: int, stock: Stock, processes: list[Process], resources: set[str], end_timestamp: float) -> list[Manager]:
    """
    Generates the population.
    :return: list[Manager]
    """
    return [generate_individual(gen_id, stock, processes, resources, index + 1, end_timestamp) for index in range(size)]

def start(stock: Stock, processes: list[Process], delay_max: int) -> None:
    """
    Starts the program's main loop.
    :return: None
    """
    end_timestamp = time.monotonic() + delay_max

    resources = get_all_resources(processes)
    population = generate_population(size=POPULATION_SIZE, gen_id=1, stock=stock, processes=processes, resources=resources, end_timestamp=end_timestamp)
    top_five_percent = get_top_five_percent()

    generation_index = 0
    while True:
        # After first generation, skips the first five percent of managers because they have already been run in previous generation
        managers_to_run = population if generation_index == 0 else population[top_five_percent:]

        # Runs manager's lifecycle
        for manager in managers_to_run:
            if is_time_up(end_timestamp):
                logger.debug("Time is up")
                break
            manager.run()

        if is_time_up(end_timestamp):
            logger.debug("Time is up")
            break

        # Sorts managers by their score in descending order
        sorted_population = sorted(population, key=lambda m: m.score, reverse=True)
        logger.info("Generation [{}] - Best score : {} | Final stock : {}"
                     .format(generation_index, sorted_population[0].score, sorted_population[0].stock))

        # Creates next population from previous one
        population = next_generation(generation_index + 1, sorted_population, stock, processes, resources, end_timestamp)

        generation_index += 1

    sorted_population = sorted(population, key=lambda m: m.score, reverse=True)
    # The Manager Of All Time
    the_moat = sorted_population[0]

    # Resets its stock before running it again, this time with printing enabled
    end_timestamp = time.monotonic() + delay_max
    the_moat.reset(stock, end_timestamp)
    the_moat.run(print_trace=True)

    logger.info("Manager Of All Time - Generation {} - Manager {} - Best score : {} | Final stock : {} | Weights : {}"
                .format(generation_index, the_moat.id, the_moat.score, the_moat.stock.inventory, the_moat.weights))
