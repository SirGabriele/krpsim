import random
from copy import deepcopy

from process import Process
from stock import Stock
from Manager import Manager

NUMBER_OF_MANAGERS_PER_GENERATION = 100
NUMBER_OF_GENERATIONS = 50

class ManagerController:
    stock: Stock
    processes: list[Process]
    managers: list[Manager]

    def __init__(self, stock: Stock, processes: list[Process], delay_max: int):
        self.stock = stock
        self.processes = processes
        self.managers = [Manager(stock, processes, delay_max) for _ in range(NUMBER_OF_MANAGERS_PER_GENERATION)]
        self.delay_max = delay_max

    def start(self) -> None:
        for i in range(NUMBER_OF_GENERATIONS):
            for manager in self.managers:
                manager.run()
            self.managers = sorted(self.managers, key=lambda m: m.score, reverse=True)
            print(f"gen : {i} : {[m.score for m in self.managers]}")
            self.managers = self.next_generation()
        print(self.managers[0].stock)

    def next_generation(self) -> list[Manager]:
        index_best_manager = int(NUMBER_OF_MANAGERS_PER_GENERATION* 5 / 100)
        index_modify_manager = int(NUMBER_OF_MANAGERS_PER_GENERATION * 20 / 100)
        new_managers = self.managers[:index_best_manager]
        modify_managers = self.managers[:index_modify_manager]

        for i in range(NUMBER_OF_MANAGERS_PER_GENERATION - index_best_manager):
            random_parent1 = random.choice(modify_managers)
            random_parent2 = random.choice(modify_managers)
            new_managers.append(Manager(
                self.stock, self.processes, self.delay_max, random_parent1, random_parent2))

        return new_managers