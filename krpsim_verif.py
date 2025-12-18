import kr_config
import traceback
import sys

from arg_parse.argparse_init import argparse_init
from file_parsing.parser import parse


def main() -> int:
    # Parser's configuration initialization
    parser = argparse_init()
    args = parser.parse_args()

    delay = int(args.delay)
    stock, processes, to_optimize = parse(args.input_file)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as err:
        if kr_config.DEBUG:
            traceback.print_exc()
        print(err)
        sys.exit(1)
