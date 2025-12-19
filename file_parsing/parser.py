import re

from custom_exceptions.FileFormatError import FileFormatError
from custom_exceptions.FileFormatOrderError import FileFormatOrderError
from process import Process
from stock import Stock
from utils.display_config_file_data import display_config_file_data


ALLOWED_CHAR_EXPR = "\w+"
NUMERIC_EXPR = "\d+"

STOCK_PATTERN_EXPR = "^(\w+):(\d+)$"
PROCESS_PATTERN_EXPR = "^(\w+):(?:\((?:(\w+:\d+(?:;\w+:\d+)*))\))?:(?:\((?:(\w+:\d+(?:;\w+:\d+)*))\))?:(\d+)$"
OPTIMIZE_PATTERN_EXPR = "^(optimize):\((?:(\w+\|time(?:;\w+\|time)*))\)$"


def parse(input_file: str) -> tuple[Stock, list[Process]]:
    stock: Stock = Stock()
    processes: list[Process] = []
    to_optimize: list[str] = []

    with open(input_file, 'r') as file:
        data = file.read()
        file_lines = data.splitlines()

    # Collects all line from the file that are not empty and not comments
    file_lines = [line for line in file_lines if line.strip() and not line.strip().startswith('#')]

    for line in file_lines:
        stock_match = re.search(STOCK_PATTERN_EXPR, line)
        process_match = re.search("".join(PROCESS_PATTERN_EXPR), line)
        optimize_match = re.search(OPTIMIZE_PATTERN_EXPR, line)

        # Stock line
        if stock_match:
            if len(processes) != 0:
                raise FileFormatOrderError()
            name, quantity = parse_stock_line(stock_match)
            stock.add(name, quantity)

        # Process line
        elif process_match:
            if len(stock.inventory) == 0:
                raise FileFormatOrderError()
            processes.append(parse_process_line(process_match))

        # Optimize line
        elif optimize_match:
            if len(to_optimize) != 0:
                raise FileFormatError(line)
            if not stock.inventory or not processes:
                raise FileFormatOrderError()
            to_optimize = parse_optimize_line(
                optimize_match,
                [key for process in processes for key in process.inputs or {}],
                [key for process in processes for key in process.outputs or {}]
            )
            stock.resources_to_optimize = to_optimize

        # Unknown line
        else:
            raise FileFormatError(line)

    if not to_optimize:
        raise FileFormatOrderError()

    display_config_file_data(len(processes), len(stock.inventory), len(stock.resources_to_optimize))

    return stock, processes


def parse_stock_line(stock_match: re.Match[str]) -> tuple[str, int] | None:
    resource = stock_match.group(1)
    quantity = int(stock_match.group(2))
    return resource, quantity


def parse_process_line(stock_match: re.Match[str]) -> Process | None:
    name = stock_match.group(1)
    inputs_str = stock_match.group(2) if stock_match.group(2) is not None else None
    outputs_str = stock_match.group(3) if stock_match.group(3) is not None else None
    delay = int(stock_match.group(4))

    inputs = parse_resource_quantity_list(inputs_str) if inputs_str else None
    outputs = parse_resource_quantity_list(outputs_str) if outputs_str else None

    return Process(name, inputs, outputs, delay)


def parse_optimize_line(optimize_match: re.Match[str], inputs: list[str], outputs: list[str]) -> list[
                                                                                                     str] | None:
    # Names of stocks to optimize are in the second group in <optimize:(stock1|time;stock2|time;[...])>
    groups = optimize_match.group(2).split(';')
    resources_to_optimize = []
    for group in groups:
        resource_to_optimize = group.split('|')[0]
        if resource_to_optimize in inputs or resource_to_optimize in outputs:
            resources_to_optimize.append(resource_to_optimize)
        else:
            return []
    return resources_to_optimize


def parse_resource_quantity_list(rq_list_str: str) -> dict:
    rq_dict: dict[str, int] = {}
    if rq_list_str:
        rq_items = rq_list_str.split(';')
        for item in rq_items:
            if item:
                resource, quantity_str = item.split(':')
                resource = resource
                quantity = int(quantity_str)
                # If key already exists, add the values together
                rq_dict[resource] = rq_dict.get(resource, 0) + quantity
    return rq_dict
