import random
from copy import deepcopy

from process import Process
from stock import Stock
from Manager import Manager

NUMBER_OF_MANAGERS_PER_GENERATION = 100
NUMBER_OF_GENERATIONS = 20

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
            #print(f"GEN {i:2.0f} - BEST SCORE: {self.managers[0].score} | STOCK: {self.managers[0].stock}")
            print([manager.score for manager in self.managers])
            if i != NUMBER_OF_GENERATIONS - 1:
                self.managers = self.next_generation()
        print(self.managers[0].stock)

    def next_generation(self) -> list[Manager]:
        index_best_manager = int(NUMBER_OF_MANAGERS_PER_GENERATION* 5 / 100)
        index_modify_manager = int(NUMBER_OF_MANAGERS_PER_GENERATION * 20 / 100)
        new_managers = []
        modify_managers = self.managers[:index_modify_manager]

        for i in range(NUMBER_OF_MANAGERS_PER_GENERATION):
            if i <= index_best_manager:
                new_manager = Manager(self.stock, self.processes, self.delay_max)
                new_manager.weights = self.managers[i].weights.copy()
                new_manager.aggressiveness_weight = self.managers[i].aggressiveness_weight
                new_manager.processes_sorted = sorted(self.processes, key=lambda p: (-self.managers[i].weights[p.name], p.name))
                new_managers.append(new_manager)
                continue
            random_parent1 = random.choice(modify_managers)
            random_parent2 = random.choice(modify_managers)
            new_managers.append(Manager(
               self.stock, self.processes, self.delay_max, random_parent1, random_parent2))

        return new_managers