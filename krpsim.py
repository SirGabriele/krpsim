import logging
import logging.config
import kr_config
import traceback
import sys

from arg_parse.argparse_init import argparse_init
from file_parsing.parser import parse

def logging_init(debug: bool):
    """Configures logger format and level."""
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s %(message)s"
    )

def main() -> int:
    # Parser's configuration initialization
    parser = argparse_init()
    args = parser.parse_args()

    # Initializes the logger
    logging_init(args.debug)

    # Handle debug mode so that the whole program has access to it
    kr_config.DEBUG = args.debug

    delay = int(args.delay)
    stock, processes = parse(args.input_file)

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as err:
        if kr_config.DEBUG:
            traceback.print_exc()
        print(err)
        sys.exit(1)
