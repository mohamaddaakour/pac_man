"""Demo: draw a real level with the renderer while the core runs."""

from __future__ import annotations

import sys

from frontend.constants import WINDOW_HEIGHT, WINDOW_WIDTH
from frontend.renderer import Renderer
from frontend.window import KEY_ESCAPE, GraphicsError, KeyEvent, Window
from pacman.config import ConfigError, load_config
from pacman.entities import Direction
from pacman.game_state import GameState
from pacman.maze_adapter import MazeError

# Temporary controls until the input handler (B4) exists.
KEYS = {
    "w": Direction.UP,
    "a": Direction.LEFT,
    "s": Direction.DOWN,
    "d": Direction.RIGHT,
}


def main(argv: list[str]) -> int:
    """Entry point"""

    path = argv[1] if len(argv) > 1 else "config.json"

    try:
        state = GameState(load_config(path))
        with Window(WINDOW_WIDTH, WINDOW_HEIGHT, "Render demo") as window:
            renderer = Renderer(window)

            def frame(dt: float) -> None:
                """Advance the core, then draw it."""
                state.update(dt)
                renderer.draw(state, dt)

            def handle_key(event: KeyEvent) -> None:
                """Steer with WASD; Esc closes the window."""
                key = event.typed_character.lower()
                if event.key_code == KEY_ESCAPE:
                    window.close()
                elif key in KEYS:
                    state.set_direction(KEYS[key])

            window.on_frame(frame)
            window.on_key(handle_key)
            window.run()
    except (ConfigError, MazeError, GraphicsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
