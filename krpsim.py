import sys

from ManagerController import ManagerController
from genetic_algo import genetic
from parser import Parser

def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python3 krpsim.py <input_file> <delay>")
    parser = Parser(sys.argv[1], sys.argv[2])
    parser.parse()
    manager_controller = ManagerController(parser.stock, parser.processes, parser.delay)
    manager_controller.start()
    return 0

if __name__ == '__main__':
    exit(main())
