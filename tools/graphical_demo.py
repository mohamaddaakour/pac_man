"""Graphical campaign demo using the existing frontend window wrapper."""

from __future__ import annotations

import sys

from frontend.window import KEY_ESCAPE, GraphicsError, Image, KeyEvent, Window
from pacman.config import ConfigError, load_config
from pacman.entities import Direction, GhostState, Position
from pacman.game_state import GameState
from pacman.highscore import Highscores, NAME_PATTERN
from tools.session import load_highscores, score_lines
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
    """Connect keyboard and frame callbacks to the campaign game core."""

    def __init__(
        self, window: Window, state: GameState,
        scores: Highscores | None = None,
    ) -> None:
        """Calculate layout and build all image buffers before the loop."""
        self.window = window
        self.state = state
        self.paused = False
        self.scores = scores or Highscores(state.config.highscore_filename)
        if scores is None:
            self.scores.load()
        self.mode = 'menu'
        self.name = ''
        self.message = ''
        self._prepare_images()
        window.on_key(self.on_key)
        window.on_close(window.close)
        window.on_frame(self.on_frame)

    def _prepare_images(self) -> None:
        """Rebuild layout and images when a level's grid changes."""
        window, state = self.window, self.state
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

    def on_key(self, event: KeyEvent) -> None:
        """Route keys to menu, name entry, or the active game."""
        key = event.typed_character.lower()
        if self.mode == 'name_entry':
            self._name_key(event)
            return
        if self.mode != 'playing':
            if self.mode == 'menu':
                if key == 'q' or event.key_code == KEY_ESCAPE:
                    self.window.close()
                elif key == 's' or event.key_code == 13:
                    self.state = GameState(self.state.config)
                    self.paused = False
                    self.message = ''
                    self._prepare_images()
                    self.mode = 'playing'
                elif key == 'h':
                    self.mode = 'highscores'
                elif key == 't':
                    self.mode = 'instructions'
            else:
                self.mode = 'menu'
            return
        if event.key_code == KEY_ESCAPE or key == 'q':
            self.mode = 'menu'  # An abandoned game does not submit a score.
        elif key == 'p':
            self.paused = not self.paused
        elif (key == 'n' and self.state.status == 'level_won'
              and not self.paused):
            self.state.next_level()
            self._prepare_images()
        elif self.paused or self.state.status != 'playing':
            return
        elif key == 'i':
            self.state.toggle_invisibility()
        elif key in KEYS:
            self.state.set_direction(KEYS[key])

    def _name_key(self, event: KeyEvent) -> None:
        """Edit a bounded name; Enter saves once, Escape skips submission."""
        if event.key_code == KEY_ESCAPE:
            self.mode = 'menu'
            self.message = ''
        elif event.key_code == 8:
            self.name = self.name[:-1]
        elif event.key_code == 13:
            if self.scores.add(self.name, self.state.score):
                self.message = 'Score saved.'
                self.mode = 'highscores'
            else:
                self.message = self.scores.last_error or 'Save failed.'
        else:
            candidate = self.name + event.typed_character
            if NAME_PATTERN.fullmatch(candidate) is not None:
                self.name = candidate

    def _draw_screen(self) -> None:
        """Draw a readable menu, table, instructions, or name prompt."""
        self.window.clear(BACKGROUND)
        if self.mode == 'menu':
            lines = ['Pac-Man', 'S / Enter: start game', 'H: top ten scores',
                     'T: instructions', 'Q / Esc: quit']
        elif self.mode == 'highscores':
            lines = ['Top ten scores', *score_lines(self.scores),
                     'Press any key to return to the menu.']
        elif self.mode == 'instructions':
            lines = ['How to play', 'WASD: move; turns wait for an exit.',
                     'Collect dots and power pellets to complete each maze.',
                     'Normal ghosts and timeouts cost a life.',
                     'Power makes ghosts edible; eating one adds points.',
                     'I: invisibility (does not prevent timeouts).',
                     'P: pause; N: next cleared level; Q / Esc: menu.',
                     'Press any key to return to the menu.']
        else:
            outcome = ('Campaign won!' if self.state.status == 'game_won'
                       else 'Game over!')
            lines = [outcome, f'Final score: {self.state.score}']
            if self.mode == 'name_entry':
                lines += [f'Name: {self.name}_',
                          '1–10 letters, digits, or spaces.',
                          'Enter: save; Backspace: erase; Escape: skip.']
            else:
                lines += ['This score does not enter the top ten.',
                          'Press any key to return to the menu.']
        for index, line in enumerate(lines):
            self.window.put_text(32, 32 + index * 32, line, WHITE)
        if self.message:
            self.window.put_text(32, 600, self.message[:80], WHITE)

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
        if self.mode != 'playing':
            self._draw_screen()
            return
        if not self.paused:
            self.state.update(dt)
        if self.state.status in ('game_won', 'game_over'):
            self.name = ''
            self.message = ''
            qualifies = self.scores.qualifies(self.state.score)
            self.mode = ('name_entry' if qualifies
                         else 'result')
            self._draw_screen()
            return
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
            f'Level: {self.state.level}/{len(self.state.levels)}   '
            f'Time: {self.state.time_left:.1f}s   Pellets: {remaining}', WHITE,
        )
        self.window.put_text(
            MARGIN, 38,
            'WASD: move   I: invisible   P: pause   N: next   Esc/Q: menu',
            WHITE,
        )
        if self.state.status == 'level_won':
            message = 'Level complete! N: next level   Esc/Q: menu.'
        elif self.state.status == 'game_won':
            message = f'Campaign won! Score: {self.state.score}. Esc/Q: menu.'
        elif self.state.status == 'game_over':
            message = 'Game over! Esc / Q: menu.'
        elif self.paused:
            message = 'Paused — P: resume   Esc/Q: menu.'
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
        config = load_config(path)
        scores = load_highscores(config, path)
        state = GameState(config)
        with Window(WIDTH, HEIGHT, 'Pac-Man') as window:
            GraphicalDemo(window, state, scores)
            window.run()
    except (ConfigError, MazeError, GraphicsError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    except Exception as exc:
        print(f'Unexpected game error: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
