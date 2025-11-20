import re
import logging

from custom_exceptions.FileFormatError import FileFormatError
from custom_exceptions.FileFormatOrderError import FileFormatOrderError
from parsing.parsed_config import ParsedConfig
from process import Process
from stock import Stock


ALLOWED_CHAR_EXPR = "\w+"
NUMERIC_EXPR = "\d+"

STOCK_PATTERN_EXPR = f"^(\w+):(\d+)$"
PROCESS_PATTERN_EXPR = "^(\w+):(?:\((?:(\w+:\d+(?:;\w+:\d+)*))\))?:(?:\((?:(\w+:\d+(?:;\w+:\d+)*))\))?:(\d+)$"
OPTIMIZE_PATTERN_EXPR = f"^(optimize):\((?:(\w+(?:;\w+)*))\)$"


def parse(input_file: str, delay: int) -> ParsedConfig:
    if not isinstance(input_file, str):
        raise TypeError("input_file must be an integer.")
    if not isinstance(delay, int):
        raise TypeError("delay must be an integer.")

    stock: Stock = Stock()
    processes: list[Process] = []
    to_optimize: list[str] = []

    try:
        with open(input_file, 'r') as file:
            data = file.read()
            file_lines = data.splitlines()
    except FileNotFoundError as err:
        raise err

    # Collects all line from the file that are not empty and not comments
    file_lines = [line for line in file_lines if line.strip() and not line.strip().startswith('#')]

    for line in file_lines:
        stock_match = re.search(STOCK_PATTERN_EXPR, line)
        process_match = re.search("".join(PROCESS_PATTERN_EXPR), line)
        optimize_match = re.search(OPTIMIZE_PATTERN_EXPR, line)

        # Stock line
        if stock_match:
            if processes:
                raise FileFormatOrderError()
            name, quantity = parse_stock_line(stock_match)
            stock.add(name, quantity)

        # Process line
        elif process_match:
            if not stock.inventory:
                raise FileFormatOrderError()
            processes.append(parse_process_line(process_match))

        # Optimize line
        elif optimize_match:
            if to_optimize:
                raise FileFormatError(line)
            if not stock.inventory or not processes:
                raise FileFormatOrderError()
            to_optimize = parse_optimize_line(optimize_match)

        # Unknown line
        else:
            raise FileFormatError(line)

    return ParsedConfig(stock, processes, to_optimize)


def parse_stock_line(stock_match: re.Match[str]) -> tuple[str, int] | None:
    resource = stock_match.group(1).strip()
    quantity = int(stock_match.group(2).strip())
    return resource, quantity


def parse_process_line(stock_match: re.Match[str]) -> Process | None:
    name = stock_match.group(1).strip()
    inputs_str = stock_match.group(2).strip() if stock_match.group(2) is not None else None
    outputs_str = stock_match.group(3).strip() if stock_match.group(3) is not None else None
    delay = int(stock_match.group(4).strip())

    inputs = parse_resource_quantity_list(inputs_str) if inputs_str else None
    outputs = parse_resource_quantity_list(outputs_str) if outputs_str else None

    return Process(name, inputs, outputs, delay)


def parse_optimize_line(optimize_match: re.Match[str]) -> list[str] | None:
    # Names of stocks to optimize are in the second group in <optimize:(stock1;stock2)>
    return optimize_match.group(2).split(';')


def parse_resource_quantity_list(rq_list_str: str) -> dict:
    rq_dict: dict[str, int] = {}
    if rq_list_str:
        rq_items = rq_list_str.split(';')
        for item in rq_items:
            if item:
                resource, quantity_str = item.split(':')
                resource = resource.strip()
                quantity = int(quantity_str.strip())
                # If key already exists, add the values together
                rq_dict[resource] = rq_dict.get(resource, 0) + quantity
    return rq_dict
