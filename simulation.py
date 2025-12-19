import logging
import random
import time

from process import Process
from stock import Stock
from Manager import Manager
from utils.is_time_up import is_time_up


POPULATION_SIZE = 200

logger = logging.getLogger()

def get_top_five_percent() -> int:
    return int(POPULATION_SIZE * 5 / 100)

def next_generation(gen_id: int, sorted_population: list[Manager], stock: Stock, processes: list[Process], delay_max: float) -> list[Manager]:
    top_five_percent = get_top_five_percent()
    remaining_managers_to_generate = POPULATION_SIZE - top_five_percent
    managers_score = [manager.score for manager in sorted_population]
    new_population = sorted_population[:top_five_percent]

    for i in range(remaining_managers_to_generate):
        # Selects two random distinct managers to breed
        parent_one, parent_two = random.choices(sorted_population, weights=managers_score, k=2)
        while parent_two == parent_one:
            parent_two = random.choices(sorted_population, weights=managers_score, k=1)[0]

        weights: dict[str, float] = {}
        for process in processes:
            # Uniform crossover. Each weight has a 50% chance to be from parent one and a 50% chance to be from parent two
            weights[process.name] = parent_one.weights[process.name] if random.random() < 0.5 else parent_two.weights[process.name]

        new_population.append(Manager(manager_id=i + 1, gen_id=gen_id, stock=stock, processes=processes, end_timestamp=delay_max, weights=weights))

    return new_population

def generate_individual(gen_id: int, stock: Stock, processes: list[Process], manager_id: int, end_timestamp: float) -> Manager:
    return Manager(manager_id=manager_id, gen_id=gen_id, stock=stock, processes=processes, end_timestamp=end_timestamp)

def generate_population(size: int, gen_id: int, stock: Stock, processes: list[Process], end_timestamp: float) -> list[Manager]:
    return [generate_individual(gen_id, stock, processes, index + 1, end_timestamp) for index in range(size)]

def start(stock: Stock, processes: list[Process], delay_max: int) -> None:
    end_timestamp = time.monotonic() + delay_max

    population = generate_population(size=POPULATION_SIZE, gen_id=1, stock=stock, processes=processes, end_timestamp=end_timestamp)
    top_five_percent = get_top_five_percent()

    generation_index = 0
    while True:
        # Runs manager's lifecycle
        for j, manager in enumerate(population):
            if is_time_up(end_timestamp):
                logger.debug("Time is up")
                break

            if generation_index == 0 or j >= top_five_percent:
                population[j].run()

        if is_time_up(end_timestamp):
            break

        # Sorts managers by their score in descending order
        sorted_population = sorted(population, key=lambda m: m.score, reverse=True)
        logger.info("Generation [{}] - Best score : {} | Final stock : {}"
                     .format(generation_index, sorted_population[0].score, sorted_population[0].stock))

        # Creates next population from previous one
        population = next_generation(generation_index + 1, sorted_population, stock, processes, end_timestamp)

        generation_index += 1

    sorted_population = sorted(population, key=lambda m: m.score, reverse=True)
    # The Manager Of All Time
    the_moat = sorted_population[0]

    the_moat.reset(stock)
    the_moat.run(print_trace=True)

    logger.info("Manager Of All Time - Generation {} - Best score : {} | Final stock : {}"
                .format(generation_index, the_moat.score, the_moat.stock))

