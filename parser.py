import re
from typing import List

from process import Process
from stock import Stock


class Parser:
    input_file: str = ""
    delay_string: str = ""
    delay: int = 0
    file_lines: List[str] = []
    stock: Stock = None
    processes: List[Process] = []

    def __init__(self, input_file, delay_string):
        self.input_file = input_file
        self.delay_string = delay_string

    def parse(self):
        try:
            self.delay = int(self.delay_string)
            with open(self.input_file, 'r') as file:
                data = file.read()
                file_lines = data.splitlines()
                file_lines = [line for line in file_lines if line.strip() != '' and not line.strip().startswith('#')]
                for line in file_lines:
                    self.parse_stock_line(line)
                    self.parse_process_line(line)

                print(f"Parsed stock: {self.stock}")
                print(f"Parsed processes: {[process.__str__() for process in self.processes]}")

        except FileNotFoundError:
            print("Input file not found")
            exit(1)
        except ValueError:
            print("Invalid delay")
            exit(1)

        pass

    def parse_stock_line(self, line: str):
        match = re.search("^([^:]+):(\d+)$", line)
        if match:
            resource = match.group(1).strip()
            quantity = int(match.group(2).strip())
            if self.stock is None:
                self.stock = Stock()
            self.stock.add(resource, quantity)

    def parse_process_line(self, line: str):
        match = re.search("^(\w+):\(((?:\w+:\d+;?)+)\):\(((?:\w+:\d+;?)+)\):(\d+)$", line)
        if match:
            name = match.group(1).strip()
            inputs_str = match.group(2).strip()
            outputs_str = match.group(3).strip()
            delay = int(match.group(4).strip())

            inputs = self.parse_resource_quantity_list(inputs_str)
            outputs = self.parse_resource_quantity_list(outputs_str)

            process = Process(name, inputs, outputs, delay)
            self.processes.append(process)

    def parse_resource_quantity_list(self, rq_list_str: str) -> dict:
        rq_dict = {}
        if rq_list_str:
            rq_items = rq_list_str.split(';')
            for item in rq_items:
                if item:
                    resource, quantity_str = item.split(':')
                    resource = resource.strip()
                    quantity = int(quantity_str.strip())
                    rq_dict[resource] = quantity
        return rq_dict
