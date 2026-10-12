"""Simple graphical phase 5 demo using the existing frontend window wrapper."""

from __future__ import annotations

import sys

from frontend.window import KEY_ESCAPE, GraphicsError, Image, KeyEvent, Window
from pacman.config import ConfigError, load_config
from pacman.entities import Direction, GhostState, Position
from pacman.game_state import GameState
from pacman.maze_adapter import MazeError

WIDTH, HEIGHT = 900, 800
HUD_HEIGHT, MARGIN = 100, 16
BACKGROUND = (8, 10, 20)
WHITE = (240, 240, 240)
KEYS = {
    'w': Direction.UP,
    'a': Direction.LEFT,
    's': Direction.DOWN,
    'd': Direction.RIGHT,
}
Color = tuple[int, int, int]


def paint_rect(
    image: Image, x: int, y: int, width: int, height: int, color: Color,
) -> None:
    """Fill an in-bounds rectangle in an image's RGBA/RGBX pixel buffer."""
    pixels = bytes((*color, 255)) * width
    for row in range(y, y + height):
        start = (row * image.width + x) * 4
        image.pixels[start:start + len(pixels)] = pixels


def circle(window: Window, size: int, radius: float, color: Color) -> Image:
    """Build one transparent circle sprite, reused on every frame."""
    image = window.new_image(size, size, opaque=False)
    center = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            if (x - center) ** 2 + (y - center) ** 2 <= radius ** 2:
                offset = (y * size + x) * 4
                image.pixels[offset:offset + 4] = bytes((*color, 255))
    return image


class GraphicalDemo:
    """Connect keyboard and frame callbacks to the phase 5 game core."""

    def __init__(self, window: Window, state: GameState) -> None:
        """Calculate layout and build all image buffers before the loop."""
        self.window = window
        self.state = state
        rows, cols = len(state.grid), len(state.grid[0])
        self.tile_size = min(
            24, (window.width - 2 * MARGIN) // cols,
            (window.height - HUD_HEIGHT - 2 * MARGIN) // rows,
        )
        if self.tile_size < 1:
            raise GraphicsError('Maze is too large for the demo window')
        size = self.tile_size
        self.offset_x = (window.width - cols * size) // 2
        self.offset_y = (
            HUD_HEIGHT + (window.height - HUD_HEIGHT - rows * size) // 2
        )

        # Paint static walls once. Frames only blit this cached background.
        self.background = window.new_image(cols * size, rows * size, True)
        paint_rect(
            self.background, 0, 0, cols * size, rows * size, BACKGROUND
        )
        for row, tiles in enumerate(state.grid):
            for col, tile in enumerate(tiles):
                if tile == 1:
                    paint_rect(
                        self.background, col * size, row * size,
                        size, size, (35, 60, 175),
                    )
        # A minimum radius keeps sprites visible on the largest mazes.
        self.dot = circle(window, size, max(0.8, size * 0.10), WHITE)
        self.super_dot = circle(window, size, max(0.8, size * 0.30), WHITE)
        self.player = circle(
            window, size, max(0.8, size * 0.42), (255, 220, 0)
        )
        self.ghosts = [
            circle(window, size, max(0.8, size * 0.40), color)
            for color in ((255, 65, 75), (255, 145, 205),
                          (65, 220, 245), (255, 165, 65))
        ]
        self.edible_ghost = circle(
            window, size, max(0.8, size * 0.40), (60, 130, 255)
        )
        window.on_key(self.on_key)
        window.on_close(window.close)
        window.on_frame(self.on_frame)

    def on_key(self, event: KeyEvent) -> None:
        """Queue WASD turns without Enter; Escape or q closes the window."""
        key = event.typed_character.lower()
        if event.key_code == KEY_ESCAPE or key == 'q':
            self.window.close()
        elif key == 'i':
            self.state.toggle_invisibility()
        elif key in KEYS:
            self.state.set_direction(KEYS[key])

    def draw_at(self, image: Image, pos: Position) -> None:
        """Convert game (row, col) into window (x, y) coordinates."""
        row, col = pos
        self.window.put_image(
            image, self.offset_x + col * self.tile_size,
            self.offset_y + row * self.tile_size,
        )

    def on_frame(self, dt: float) -> None:
        """Advance the core and draw the latest state and HUD."""
        if self.window.closed:
            return
        self.state.update(dt)
        self.window.clear(BACKGROUND)
        self.window.put_image(self.background, self.offset_x, self.offset_y)
        for pos in self.state.pacgums:
            self.draw_at(self.dot, pos)
        for pos in self.state.super_pacgums:
            self.draw_at(self.super_dot, pos)
        for image, ghost in zip(self.ghosts, self.state.ghosts):
            if ghost.state == GhostState.EATEN:
                continue
            if ghost.state == GhostState.EDIBLE:
                image = self.edible_ghost
            self.draw_at(image, ghost.pos)
        self.draw_at(self.player, self.state.player.pos)
        remaining = len(self.state.pacgums) + len(self.state.super_pacgums)
        self.window.put_text(
            MARGIN, 10,
            f'Score: {self.state.score}   Lives: {self.state.lives}   '
            f'Level: {self.state.level}   Pellets: {remaining}', WHITE,
        )
        self.window.put_text(
            MARGIN, 38,
            'WASD: move   I: invisibility   Esc / Q: quit', WHITE,
        )
        if self.state.status == 'level_won':
            message = 'Level complete! Esc / Q to close.'
        elif self.state.status == 'game_over':
            message = 'Game over! Esc / Q to close.'
        else:
            message = (
                f'Invisible: {self.state.invisible}   '
                f'Power: {self.state.edible_timer:.1f}s   '
                f'Grace: {self.state.grace_timer:.1f}s'
            )
        self.window.put_text(MARGIN, 66, message, WHITE)


def main(argv: list[str]) -> int:
    """Open the standalone graphical demo with one optional config path."""
    if len(argv) > 2:
        print('Usage: python -m tools.graphical_demo [config.json]',
              file=sys.stderr)
        return 1
    path = argv[1] if len(argv) > 1 else 'config.json'
    try:
        state = GameState(load_config(path))
        with Window(WIDTH, HEIGHT, 'Pac-Man — Phase 5') as window:
            GraphicalDemo(window, state)
            window.run()
    except (ConfigError, MazeError, GraphicsError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
