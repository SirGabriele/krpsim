import sys
from parser import Parser

def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python3 krpsim.py <input_file> <delay>")
    parser = Parser(sys.argv[1], sys.argv[2])
    parser.parse()
    return 0

if __name__ == '__main__':
    exit(main())
