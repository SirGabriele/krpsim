import traceback
import sys
import re

import kr_config
from arg_parse.argparse_init import argparse_verif_init
from custom_exceptions.NotEnoughResourcesError import NotEnoughResourcesError
from custom_exceptions.ProcessNameNotFoundError import ProcessNameNotFoundError
from custom_exceptions.ImpossibleCycleOrderError import ImpossibleCycleOrderError
from custom_exceptions.InvalidTraceLineError import InvalidTraceLineError
from file_parsing.parser import parse, NUMERIC_EXPR, ALLOWED_CHAR_EXPR
from process import Process
from stock import Stock

TRACE_LINE_FORMAT = f"^({NUMERIC_EXPR}):({ALLOWED_CHAR_EXPR})$"

def parse_trace_line(trace_line: str, processes: list[Process]) -> tuple[int, str]:
    """
    Parse a single line from the trace file.
    :param trace_line: Line to parse.
    :param processes: List of available processes.
    :return: Tuple of (cycle, process_name).
    :raises InvalidTraceLineError: If the line format is invalid.
    :raises ValueError: If the cycle is not a valid integer.
    :raises ProcessNameNotFoundError: If the process name is not found in the list
    """
    match = re.search(TRACE_LINE_FORMAT, trace_line)
    if not match:
        raise InvalidTraceLineError(trace_line)
    cycle = match.group(1)
    process_name = match.group(2)
    process_exists = any(p.name == process_name for p in processes)
    if not process_exists:
        raise ProcessNameNotFoundError(process_name)
    return int(cycle), process_name


def parse_trace(trace_file: str, processes: list[Process]) -> list[tuple[int, str]] | None:
    """
    Parse the entire trace file.
    :param trace_file: Path to the trace file.
    :param processes: List of available processes.
    :return: List of tuples containing (cycle, process_name) or None if an error occurs.
    """
    try:
        parsed_lines: list[tuple[int, str]] = []
        with open(trace_file, 'r') as trace:
            last_cycle = 0
            for index, line in enumerate(trace):
                cycle, process_name = parse_trace_line(line.strip(), processes)
                if cycle < last_cycle:
                    raise ImpossibleCycleOrderError(cycle, last_cycle, index + 1)
                parsed_lines.append((cycle, process_name))
                last_cycle = cycle
        return parsed_lines
    except Exception as e:
        print(e)
        return None

class KrpSimVerifier:
    """
    Class to verify the simulation based on the provided stock and processes.
    :param stock: Initial stock of resources.
    :param processes: List of available processes.
    """
    def __init__(self, stock: Stock, processes: list[Process]):
        self.stock = stock
        self.processes = processes
        self.current_cycle = 0
        self.running_processes: list[tuple[int, Process]] = []  # (end_cycle, Process)

    def __remove_from_stock(self, items: dict[str, int]):
        """
        Remove items from stock.
        :param items: Items to remove with their quantities.
        :return: None
        """
        if items is None:
            return

        for item, qty in items.items():
            self.stock.consume(item, qty)

    def __add_to_stock(self, items: dict[str, int]):
        """
        Add items to stock.
        :param items: Items to add with their quantities.
        :return: None
        """
        if items is None:
            return

        for item, qty in items.items():
            self.stock.add(item, qty)

    def __does_stock_have_inputs(self, inputs: dict[str, int]) -> bool:
        """
        Check if stock has enough quantity for all input items.
        :param inputs: Input items with their required quantities.
        :return: True if stock has enough quantity for all items, False otherwise.
        """
        if inputs is None:
            return True

        for item, qty in inputs.items():
            if self.stock.get_quantity(item) < qty:
                return False
        return True

    def __complete_processes(self, cycle_limit: int):
        """
        Complete processes that finish at or before cycle_limit.
        :param cycle_limit: The cycle limit up to which processes should be completed.
        :return: None
        """
        finished = [rp for rp in self.running_processes if rp[0] <= cycle_limit]

        for end_cycle, proc in finished:
            self.__add_to_stock(proc.outputs)
            self.running_processes.remove((end_cycle, proc))

    def run(self, parsed_lines: list[tuple[int, str]]) -> bool:
        """
        Run the simulation verifier with the parsed trace lines.
        :param parsed_lines: List of tuples containing (cycle, process_name).
        :return: True if simulation completes successfully, False otherwise.
        """
        try:
            for cycle, process_name in parsed_lines:
                self.current_cycle = cycle
                self.__complete_processes(self.current_cycle)
                process = next(p for p in self.processes if p.name == process_name)
                if not self.__does_stock_have_inputs(process.inputs):
                    raise NotEnoughResourcesError(process_name, self.stock.inventory, process.inputs)
                self.__remove_from_stock(process.inputs)
                end_cycle = self.current_cycle + process.delay
                self.running_processes.append((end_cycle, process))
            if self.running_processes:
                for end_cycle, proc in self.running_processes:
                    if end_cycle > kr_config.MAX_CYCLE_PER_MANAGER:
                        break
                    self.current_cycle = end_cycle
                    self.__add_to_stock(proc.outputs)
                self.running_processes.clear()
            return True
        except Exception as e:
            print(e)
            return False


def print_final_info(end_cycle: int, stock_inventory: dict[str, int]) -> None:
    """
    Print the final information of the simulation.
    :param end_cycle: Current cycle of the simulation.
    :param stock_inventory: Final stock inventory.
    :return: None
    """
    print(f"Simulation ended at cycle {end_cycle}.")
    print("Final stock :")
    for resource, quantity in stock_inventory.items():
        print(f"- {resource}: {quantity}")

def main() -> int:
    parser = argparse_verif_init()
    args = parser.parse_args()

    stock, processes = parse(args.input_file)
    parsed_lines = parse_trace(args.trace_file, processes)

    exit_code = 0
    if not parsed_lines:
        print_final_info(0, stock.inventory)
        return 0

    verifier = KrpSimVerifier(stock, processes)
    if not verifier.run(parsed_lines):
        exit_code = 1

    if exit_code == 0:
        print("Simulation completed successfully.")

    print_final_info(verifier.current_cycle, verifier.stock.inventory)
    return exit_code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as err:
        traceback.print_exc()
        print(err)
        sys.exit(1)