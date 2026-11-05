"""Launch the graphical game: python3 pac-man.py <config.json>."""

import sys
from pacman.config import Config, ConfigError, load_config
from pacman.highscore import Highscores
from tools.session import load_highscores


def _run(argv: list[str]) -> int:
    """Check the argument, load the config and scores, then play.

    Each expected failure prints one readable line and returns 1.
    """
    if len(argv) != 2:
        print('Usage: python3 pac-man.py config.json', file=sys.stderr)
        return 1
    try:
        config: Config = load_config(argv[1])
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    highscores: Highscores = load_highscores(config, argv[1])
    try:
        from frontend.window import Window, GraphicsError
        from frontend.app import App
        from frontend.constants import WINDOW_WIDTH, WINDOW_HEIGHT
    except ImportError as e:
        print(f"Error: missing package '{e.name}', run make install",
              file=sys.stderr)
        return 1
    try:
        with Window(WINDOW_WIDTH, WINDOW_HEIGHT, "Pac-Man") as window:
            App(window, config, highscores).run()
    except GraphicsError as e:
        print(f"Error: cannot open the game window: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str]) -> int:
    """Run the game, turning anything unexpected into one clean line.

    No traceback is ever shown: Ctrl+C exits with 130 and any other
    error with 1.

    Args:
        argv: The command line (sys.argv).

    Returns:
        The exit code, 0 after a normal quit.
    """
    try:
        result: int = _run(argv)
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"Unexpected error: {e.__class__.__name__}: {e}",
              file=sys.stderr)
        return 1
    return result


if __name__ == '__main__':
    sys.exit(main(sys.argv))
