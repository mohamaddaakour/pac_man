"""Launch the terminal application with exactly one JSON config argument."""

import sys

from tools.cli_demo import main


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python3 pac-man.py config.json', file=sys.stderr)
        sys.exit(1)
    sys.exit(main(sys.argv))
