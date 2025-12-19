import kr_config
import traceback
import sys
import re

from arg_parse.argparse_init import  argparse_verif_init
from custom_exceptions.NotEnoughResourcesError import NotEnoughResourcesError
from custom_exceptions.ProcessNameNotFoundError import ProcessNameNotFoundError
from custom_exceptions.ImpossibleCycleOrderError import ImpossibleCycleOrderError
from custom_exceptions.InvalidTraceLineError import InvalidTraceLineError
from custom_exceptions.ProcessNameNotFoundError import ProcessNameNotFoundError
from file_parsing.parser import parse, NUMERIC_EXPR, ALLOWED_CHAR_EXPR
from process import Process
from stock import Stock

TRACE_LINE_FORMAT = f"^({NUMERIC_EXPR}):({ALLOWED_CHAR_EXPR})$"
last_checked_cycle = 0

def remove_from_stock(stock: Stock, items: dict[str, int]):
    for item, qty in items.items():
        stock.consume(item, qty)

def add_to_stock(stock: Stock, items: dict[str, int]):
    for item, qty in items.items():
        stock.add(item, qty)

def dose_stock_have_inputs(stock: Stock, inputs: dict[str, int]) -> bool:
    for item, qty in inputs.items():
        if stock.get_quantity(item) < qty:
            return False
    return True

def print_os_error_message(error: OSError):
    if isinstance(error, FileNotFoundError):
        print(f"File not found: {error.filename}")
    elif isinstance(error, PermissionError):
        print(f"Permission denied: {error.filename}")
    else:
        print(f"OS error ({error.errno}): {error.strerror} - {error.filename}")

def print_error_message(error: BaseException):
    print(error)
    return
    if isinstance(error, OSError):
        print_os_error_message(error)
    elif (isinstance(error, InvalidTraceLineError) or
          isinstance(error, ProcessNameNotFoundError) or
          isinstance(error, ImpossibleCycleOrderError)):
        print(error)
    else:
        print(f"Error: {error}")

def parse_trace_line(trace_line: str, processes: list[Process]) -> tuple[int, str]:
    """
    Parse a single line of the trace file.

    Throws InvalidTraceLineError if the line is not valid.
    Throws ValueError if the cycle is not an integer.
    Throws ProcessNotFoundError if the process name is not recognized.
    :param processes:  List of valid processes.
    :param trace_line: The line from the trace file.
    :return: A tuple containing the cycle and the process name
    """
    match = re.search(TRACE_LINE_FORMAT, trace_line)
    if not match:
        raise InvalidTraceLineError(trace_line)
    cycle = match.group(1)
    if not cycle.isdigit():
        raise ValueError(f"Cycle '{cycle}' is not a valid integer.")
    process_name = match.group(2)
    process_exists = any(p.name == process_name for p in processes)
    if not process_exists:
        raise ProcessNameNotFoundError(process_name)
    return int(cycle), process_name



def parse_trace(trace_file: str,processes: list[Process]) -> list[tuple[int, str]] | None:
    try:
        parsed_lines: list[tuple[int, str]] = []
        with open(trace_file) as trace:
            last_cycle = 0
            for index, line in enumerate(trace):
                cycle, process_name = parse_trace_line(line.strip(), processes)
                if cycle < last_cycle:
                    raise ImpossibleCycleOrderError(cycle, last_cycle, index + 1)
                parsed_lines.append((cycle, process_name))
                last_cycle = cycle
        return parsed_lines
    except Exception as e:
        print_error_message(e)
        return None

def simulate_trace(parsed_lines: list[tuple[int, str]], processes: list[Process], stock: Stock) -> bool:
    try:
        processes_running: list[tuple[int, Process]]= []  # List of (end_cycle, Process)
        global last_checked_cycle
        for cycle, process_name in parsed_lines:
            last_checked_cycle = cycle
            # First, check if any process has finished by this cycle
            processes_to_complete = [pr for pr in processes_running if pr[0] <= cycle]
            for end_cycle, proc in processes_to_complete:
                add_to_stock(stock, proc.outputs)
                processes_running.remove((end_cycle, proc))

            # Now, try to start the new process
            process = next(p for p in processes if p.name == process_name)
            if not dose_stock_have_inputs(stock, process.inputs):
                raise NotEnoughResourcesError(process_name, stock.inventory, process.inputs)
            remove_from_stock(stock, process.inputs)
            end_cycle = cycle + process.delay
            processes_running.append((end_cycle, process))
        for end_cycle, proc in processes_running:
            if end_cycle > last_checked_cycle:
                last_checked_cycle = end_cycle
            add_to_stock(stock, proc.outputs)
        return True
    except Exception as e:
        print_error_message(e)
        return False

def print_final_info(stock :Stock):
    print(f"Simulation ended at cycle {last_checked_cycle}.")
    print("Final stock :")
    for resource, quantity in stock.inventory.items():
        print(f"- {resource}: {quantity}")


def main() -> int:
    parser = argparse_verif_init()
    args = parser.parse_args()

    stock, processes, _ = parse(args.input_file)
    parsed_lines = parse_trace(args.trace_file, processes)
    exit_code = 0
    if not parsed_lines:
        exit_code = 1
    else:
        if not simulate_trace(parsed_lines, processes, stock):
            exit_code = 1
    if exit_code == 0:
        print("Simulation completed successfully.")
    print_final_info(stock)
    return exit_code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as err:
        if kr_config.DEBUG:
            traceback.print_exc()
        print(err)
        sys.exit(1)
