import logging
import random
import time
from multiprocessing import Pool
from os import cpu_count

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

def next_generation(gen_id: int, sorted_population: list[Manager], stock: Stock, processes: list[Process], end_timestamp: float) -> list[Manager]:
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

    score_min = min(managers_score)
    positive_manager_scores = []
    for manager_score in managers_score:
        positive_manager_scores.append(manager_score + abs(score_min))
    for i in range(remaining_managers_to_generate):
        # Selects two random distinct managers to breed
        parent_one, parent_two = random.choices(sorted_population, weights=positive_manager_scores, k=2)
        while parent_two == parent_one:
            parent_two = random.choices(sorted_population, weights=positive_manager_scores, k=1)[0]

        weights: dict[str, float] = {}
        for process in processes:
            # Uniform crossover. Each weight has a 50% chance to be from parent one and a 50% chance to be from parent two
            weights[process.name] = parent_one.weights[process.name] if random.random() < 0.5 else parent_two.weights[process.name]
        if random.random() < 0.5:
            random_wait_uuid = parent_one.random_wait_uuid
            weights[random_wait_uuid] = parent_one.weights[random_wait_uuid]
        else:
            random_wait_uuid = parent_two.random_wait_uuid
            weights[random_wait_uuid] = parent_two.weights[random_wait_uuid]
        new_population.append(generate_individual(manager_id=i + 1, gen_id=gen_id, stock=stock, processes=processes, end_timestamp=end_timestamp, weights=weights))

    return new_population

def generate_individual(gen_id: int, stock: Stock, processes: list[Process], manager_id: int, end_timestamp: float, weights: dict[str, float] | None = None, random_wait_uuid: str | None = None) -> Manager:
    """
    Generates one individual.
    :return: Manager
    """
    return Manager(manager_id=manager_id, gen_id=gen_id, stock=stock, processes=processes, end_timestamp=end_timestamp, weights=weights, random_wait_uuid=random_wait_uuid)

def generate_population(size: int, gen_id: int, stock: Stock, processes: list[Process], end_timestamp: float) -> list[Manager]:
    """
    Generates the population.
    :return: list[Manager]
    """
    return [generate_individual(gen_id, stock, processes, index + 1, end_timestamp) for index in range(size)]


def run_manager_simulation(manager: Manager) -> Manager:
    if is_time_up(manager.end_timestamp):
        return manager
    manager.run()
    return manager

def start(stock: Stock, processes: list[Process], delay_max: int) -> None:
    """
    Starts the program's main loop.
    :return: None
    """
    end_timestamp = time.monotonic() + delay_max

    population = generate_population(size=POPULATION_SIZE, gen_id=1, stock=stock, processes=processes, end_timestamp=end_timestamp)
    top_five_percent = get_top_five_percent()

    generation_index = 0
    with Pool(processes=cpu_count()) as pool:
        while True:
            if is_time_up(end_timestamp):
                logger.debug("Time is up (Start of loop)")
                break

            if generation_index == 0:
                managers_to_run = population
                managers_skipped = []
            else:
                managers_skipped = population[:top_five_percent]
                managers_to_run = population[top_five_percent:]

            ran_managers = pool.map(run_manager_simulation, managers_to_run)
            population = managers_skipped + ran_managers

            sorted_population = sorted(population, key=lambda m: m.score, reverse=True)
            print("Generation {} - Best score : {} | Final stock : {}\033[K".format(generation_index, sorted_population[0].score, sorted_population[0].stock.inventory), end="\r", flush=True)

            population = next_generation(generation_index + 1, sorted_population, stock, processes,
                                         end_timestamp)

            generation_index += 1
    sorted_population = sorted(population, key=lambda m: m.score, reverse=True)
    # The Manager Of All Time
    the_moat = sorted_population[0]

    # Resets its stock before running it again, this time with printing enabled
    end_timestamp = time.monotonic() + delay_max
    the_moat.reset(stock, end_timestamp)
    the_moat.run(print_trace=True)

    logger.info("Manager Of All Time - Generation {} - Best score : {} | Final stock : {}"
                .format(generation_index, the_moat.score, the_moat.stock.inventory))
