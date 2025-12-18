import argparse
import os


def existing_file(path: str) -> str:
    """Helper function used to validate the file_input argument."""
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"File '{path}' does not exist")
    return path


def argparse_init():
    parser = argparse.ArgumentParser(
        description='Run krpsim program with an input file and a delay',
        usage="python3.10 krpsim.py <input_file> <delay>"
    )
    parser.add_argument('input_file', type=existing_file, help='Path to the input file')
    parser.add_argument('delay', type=int, help='Numeric delay to not exceed')
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")

    return parser

def argparse_verif_init():
    parser = argparse.ArgumentParser(
        description='Run krpsim_verif program with an input file and a trace file',
        usage="python3.10 krpsim_verif.py <input_file> <trace_file>"
    )
    parser.add_argument('input_file', type=existing_file, help='path to the input file')
    parser.add_argument('trace_file', type=int, help='path to the trace file')
    return parser
