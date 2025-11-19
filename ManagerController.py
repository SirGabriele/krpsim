from process import Process
from stock import Stock
from Manager import Manager

NUMBER_OF_MANAGERS_PER_GENERATION = 1

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
        for manager in self.managers:
            manager.run()