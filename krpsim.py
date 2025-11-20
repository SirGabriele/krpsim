import argparse
import logging
import logging.config
import kr_config
import traceback
import sys
import os

from parsing.parsed_config import ParsedConfig
from parsing.parser import parse


def configure_logging(debug: bool):
    """Configures logger format and level."""
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s %(message)s"
    )


def existing_file(path: str) -> str:
    """Helper function used to validate the file_input argument."""
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"File '{path}' does not exist")
    return path


def main() -> int:
    # Parser's configuration initialization
    parser = argparse.ArgumentParser(
        description='Run krpsim program with an input file and a delay',
        usage="python3.10 krpsim.py <input_file> <delay>"
    )
    parser.add_argument('input_file', type=existing_file, help='Path to the input file')
    parser.add_argument('delay', type=int, help='Numeric delay to not exceed')
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()
    configure_logging(args.debug)

    kr_config.DEBUG = args.debug
    parsed_config: ParsedConfig = parse(args.input_file, args.delay)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as err:
        if kr_config.DEBUG:
            traceback.print_exc()
        print(err)
        sys.exit(1)
