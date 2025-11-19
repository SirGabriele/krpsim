import random
from typing import List

from process import Process
from Manager import Manager


def choose_process(processes: List[Process], process_in_progress: dict[str, int], stock: dict[str, int]):
    for process in processes:
        if process.name in process_in_progress:
            continue
        elif check_stock_process(stock, process):
            remove_stock_from_process(process, stock)
            process_in_progress[process.name] = process.delay


def remove_stock_from_process(process: Process, stock: dict[str, int]):
    for input in process.inputs.keys():
        if input in stock.keys():
            stock[input] -= process.inputs[input]


def check_stock_process(stock: dict[str, int], process: Process):
    stock_available = list(s for s in stock if stock[s] > 0)
    for input, requested_quantity in process.inputs.items():
        if input not in stock_available or stock[input] < requested_quantity:
            return False
    return True


def process_in_progress(process_in_progress: dict[str, int]):
    for process in process_in_progress:
        process_in_progress[process] -= 1


def result_process(stock: dict[str, int], processes: List[Process], processes_in_progress: dict[str, int]):
    temp_processes_in_progress: dict[str, int] = processes_in_progress.copy()
    for process in temp_processes_in_progress:
        if temp_processes_in_progress[process] != 0:
            continue
        select_process = list(p for p in processes if p.name == process)
        for current_process in select_process:
            for output, quantity in current_process.outputs.items():
                stock[output] += quantity
            processes_in_progress.pop(current_process.name)


def do_process(manager: dict[str, float], processes: list[Process]) -> int:
    stock: dict[str, int] = {
        'result': 0,
        'clock': 1,
        'second': 0,
        'minute': 0,
        'hour': 0,
        'day': 0,
        'year': 0,
        'dream': 0,
    }

    process_sorted = sorted(processes, key=lambda p: manager.get(p.name, 0))

    processes_in_progress: dict[str, int] = {}

    for delay in range(10000):
        choose_process(process_sorted, processes_in_progress, stock)

        process_in_progress(processes_in_progress)

        result_process(stock, process_sorted, processes_in_progress)

    return stock['year']


def genetic(processes: list[Process]) -> int:
    manager: dict[str, float] = {}


    for i in range(100):
        for process in processes:
            manager[process.name] = random.random()
            do_process(manager, processes)

    return 0
