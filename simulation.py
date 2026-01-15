import logging
import random
import time
import os
from collections import deque
from typing import Any
from concurrent.futures import ProcessPoolExecutor, as_completed
from kr_config import POPULATION_SIZE
from process import Process
from stock import Stock
from Manager import Manager
from utils.is_time_up import is_time_up

logger = logging.getLogger()


def generate_resources_heatmap(processes: list[Process], resources_to_optimize: set[str]) -> dict[str, float]:
    producers_map: dict[str, list[Process]] = {}

    # Builds a map of which resource is produced by which processes
    for p in processes:
        if p.outputs:
            for output_name in p.outputs.keys():
                if output_name not in producers_map:
                    producers_map[output_name] = []
                producers_map[output_name].append(p)

    resources_heatmap: dict[str, float] = {}
    queue = deque()

    TARGET_VALUE = 1000000000.0
    DECAY_FACTOR = 0.0001

    # Initializes queue with target resources
    for target in resources_to_optimize:
        if target == "time":
            continue

        resources_heatmap[target] = TARGET_VALUE
        queue.append(target)

    while queue:
        # At each step, pops a resource from the queue and propagates its value to its ingredients
        current_resource = queue.popleft()
        current_value = resources_heatmap[current_resource]

        if current_resource in producers_map:
            producing_processes = producers_map[current_resource]

            for process in producing_processes:
                if not process.inputs:
                    continue

                for ingredient in process.inputs.keys():

                    next_value = current_value * DECAY_FACTOR

                    if ingredient not in resources_heatmap or resources_heatmap[ingredient] < next_value:
                        resources_heatmap[ingredient] = next_value
                        queue.append(ingredient)

    return resources_heatmap


def get_top_five_percent() -> int:
    """
    Calculates the amount of individuals that equals five percent of the population.
    :return: int
    """
    return int(POPULATION_SIZE * 5 / 100)


def next_generation(gen_id: int, sorted_population: list[Manager], stock: Stock, processes: list[Process],
                    resources: set[str], resources_heatmap: dict[str, float], delay_max: float) -> list[Manager]:
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
        scores = [m.score for m in sorted_population]
        min_score = min(scores)
        positive_weights = [(s - min_score) + 1 for s in scores]
        parent_one, parent_two = random.choices(sorted_population, weights=positive_weights, k=2)
        while parent_two == parent_one:
            parent_two = random.choices(sorted_population, weights=positive_weights, k=1)[0]

        weights: dict[str, float] = {}
        for resource in resources:
            # Uniform crossover. Each weight has a 50% chance to be from parent one and a 50% chance to be from parent two
            weights[resource] = parent_one.weights[resource] if random.random() < 0.5 else parent_two.weights[resource]

        new_population.append(
            generate_individual(manager_id=i + 1, gen_id=gen_id, stock=stock, processes=processes, resources=resources,
                                resources_heatmap=resources_heatmap, end_timestamp=end_timestamp, weights=weights))

    return new_population


def generate_individual(gen_id: int, stock: Stock, processes: list[Process], resources: set[str],
                        resources_heatmap: dict[str, float], manager_id: int, end_timestamp: float,
                        weights: dict[str, float] | None = None) -> Manager:
    """
    Generates one individual.
    :return: Manager
    """
    return Manager(manager_id=manager_id, gen_id=gen_id, stock=stock, processes=processes, resources=resources,
                   resources_heatmap=resources_heatmap, end_timestamp=end_timestamp, weights=weights)


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


def generate_population(size: int, gen_id: int, stock: Stock, processes: list[Process], resources: set[str],
                        resources_heatmap: dict[str, float], end_timestamp: float) -> list[Manager]:
    """
    Generates the population.
    :return: list[Manager]
    """
    return [generate_individual(gen_id, stock, processes, resources, resources_heatmap, index + 1, end_timestamp) for
            index in range(size)]


def start(stock: Stock, processes: list[Process], delay_max: int) -> None:
    """
    Starts the program's main loop with Multi-Threading.
    :return: None
    """
    end_timestamp = time.monotonic() + delay_max

    resources = get_all_resources(processes)
    resources_heatmap = generate_resources_heatmap(processes, stock.resources_to_optimize)
    population = generate_population(size=POPULATION_SIZE, gen_id=1, stock=stock, processes=processes,
                                     resources=resources, resources_heatmap=resources_heatmap,
                                     end_timestamp=end_timestamp)
    top_five_percent = get_top_five_percent()

    generation_index = 0

    # Use max_workers=None to let Python decide based on CPU count (usually cpu_count + 4)
    # or set a specific number like os.cpu_count()
    max_workers = os.cpu_count() or 4

    # We initialize the executor once to reuse threads
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        while True:
            if is_time_up(end_timestamp):
                logger.debug("Time is up (before generation start)")
                break

            # After first generation, skips the first five percent of managers because they have already been run in previous generation
            managers_to_run = population if generation_index == 0 else population[top_five_percent:]

            # Submit all manager runs to the thread pool
            futures = []
            for manager in managers_to_run:
                # We submit the manager.run method directly
                futures.append(executor.submit(manager.run))

            # Wait for all threads to complete for this generation
            # We use as_completed to handle them as they finish, but we essentially need to wait for all
            # before sorting/breeding.
            early_exit = False
            for future in as_completed(futures):
                # Optional: Check if time is up during processing to cancel remaining?
                # Thread cancellation is tricky, usually better to let them finish the current batch
                if is_time_up(end_timestamp) and not early_exit:
                    logger.debug("Time is up (during generation execution)")
                    early_exit = True
                    # In a real scenario, we might want to cancel pending futures here
                    # but ThreadPoolExecutor doesn't support easy hard-kill of running threads.
                    # We just stop processing the loop logic.

            if early_exit:
                break

            # Sorts managers by their score in descending order
            sorted_population = sorted(population, key=lambda m: m.score, reverse=True)
            logger.info("Generation [{}] - Best score : {} | Final stock : {}"
                        .format(generation_index, sorted_population[0].score, sorted_population[0].stock))

            if is_time_up(end_timestamp):
                break

            # Creates next population from previous one
            population = next_generation(generation_index + 1, sorted_population, stock, processes, resources,
                                         resources_heatmap, end_timestamp)

            generation_index += 1

    # Final logic after loop
    sorted_population = sorted(population, key=lambda m: m.score, reverse=True)
    # The Manager Of All Time
    the_moat = sorted_population[0]

    # Resets its stock before running it again, this time with printing enabled
    end_timestamp = time.monotonic() + delay_max
    the_moat.reset(stock, end_timestamp)
    the_moat.run(print_trace=True)

    logger.info("Manager Of All Time - Generation {} - Manager {} - Best score : {} | Final stock : {} | Weights : {}"
                .format(generation_index, the_moat.id, the_moat.score, the_moat.stock.inventory, the_moat.weights))