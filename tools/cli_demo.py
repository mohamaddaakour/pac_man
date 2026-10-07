"""Terminal demo of the game core."""

from __future__ import annotations

import sys
# from pathlib import Path

from pacman.config import ConfigError, load_config

def main(argv: list[str]) -> int:
    """Entry point"""

    if len(argv) > 1:
        path = argv[1]
    else:
        path = "config.json"

    try:
        config = load_config(path)
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    
    print("Resolved configuration:")

    for field, value in vars(config).items():
        print(f"{field}: {value}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))