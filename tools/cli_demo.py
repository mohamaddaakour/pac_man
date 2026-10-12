"""Play the first level with line-based terminal input."""

from __future__ import annotations

import sys

from pacman.config import ConfigError, load_config
from pacman.entities import Direction
from pacman.game_state import GameState
from pacman.maze_adapter import MazeError

KEYS = {
    'w': Direction.UP,
    'a': Direction.LEFT,
    's': Direction.DOWN,
    'd': Direction.RIGHT,
}


def render_ascii(state: GameState) -> str:
    """Draw pellets, then ghosts, then the player above the grid."""
    canvas = [['#' if tile else ' ' for tile in row] for row in state.grid]
    for row, col in state.pacgums:
        canvas[row][col] = '.'
    for row, col in state.super_pacgums:
        canvas[row][col] = 'O'
    for number, ghost in enumerate(state.ghosts, start=1):
        row, col = ghost.pos
        canvas[row][col] = str(number)
    row, col = state.player.pos
    canvas[row][col] = 'P'
    return '\n'.join(''.join(row) for row in canvas)


def main(argv: list[str]) -> int:
    """Play one level; initialization errors exit with a readable message."""
    path = argv[1] if len(argv) > 1 else 'config.json'
    try:
        state = GameState(load_config(path))
    except (ConfigError, MazeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1

    print('WASD + Enter: turn; Enter: continue; q: quit.')
    print('Each accepted command advances 0.15 simulated seconds.')
    print('Ghosts are stationary and harmless in phase 3.')
    print('Legend: # wall, . pacgum, O super-pacgum, P player, 1–4 ghosts.')
    print('Ghosts cover their starting super-pacgums until you visit them.')
    print(f'Tile grid: {len(state.grid)} rows x {len(state.grid[0])} columns')
    try:
        while True:
            print(render_ascii(state))
            print(
                f'Score: {state.score} | Lives: {state.lives} | '
                f'Remaining: {len(state.pacgums) + len(state.super_pacgums)}'
            )
            if state.status == 'level_won':
                print('Level complete! Level progression comes in phase 6.')
                return 0
            command = input('Move [w/a/s/d, Enter, q]: ').strip().lower()
            if command == 'q':
                return 0
            if command in KEYS:
                state.set_direction(KEYS[command])
            elif command:
                print('Use w, a, s, d, Enter, or q.')
                continue  # Invalid input does not advance simulation time.
            state.update(state.STEP_TIME)
    except (EOFError, KeyboardInterrupt):
        print('\nDemo closed.')
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
