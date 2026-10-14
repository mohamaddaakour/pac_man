"""Play the campaign with line-based terminal input."""

from __future__ import annotations

import sys

from pacman.config import ConfigError, load_config
from pacman.entities import Direction, GhostState
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
        if ghost.state != GhostState.EATEN:
            canvas[row][col] = (
                'e' if ghost.state == GhostState.EDIBLE else str(number)
            )
    row, col = state.player.pos
    canvas[row][col] = 'P'
    return '\n'.join(''.join(row) for row in canvas)


def main(argv: list[str]) -> int:
    """Play a campaign; initialization errors exit with a readable message."""
    path = argv[1] if len(argv) > 1 else 'config.json'
    try:
        state = GameState(load_config(path))
    except (ConfigError, MazeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1

    print('WASD + Enter: turn; Enter: continue; i: invisibility; q: quit.')
    print('P: pause/resume; N: next cleared level. Each move advances 0.15s.')
    paused = False
    print('Ghosts chase normally and flee when edible; I prevents damage.')
    print('Legend: # wall, . pacgum, O super-pacgum, P player, 1–4 ghosts.')
    print('e = edible ghost; eaten ghosts disappear until they respawn.')
    print(f'Tile grid: {len(state.grid)} rows x {len(state.grid[0])} columns')
    try:
        while True:
            print(render_ascii(state))
            remaining = len(state.pacgums) + len(state.super_pacgums)
            print(
                f'Level: {state.level}/{len(state.levels)} | '
                f'Time: {state.time_left:.1f}s | '
                f'Score: {state.score} | Lives: {state.lives} | '
                f'Remaining: {remaining} | '
                f'Invisible: {state.invisible} | '
                f'Power: {state.edible_timer:.1f}s '
                f'| Grace: {state.grace_timer:.1f}s'
            )
            if state.status == 'level_won':
                print('Level complete! Use N to advance or Q to quit.')
            if state.status == 'game_won':
                print(f'Campaign won! Final score: {state.score}')
                return 0
            if state.status == 'game_over':
                print(f'Game over! Final score: {state.score}')
                return 0
            if paused:
                print('Paused — P resumes, Q quits.')
            command = input('Command [WASD, Enter, I, P, N, Q]: ')
            command = command.strip().lower()
            if command == 'q':
                return 0
            if command == 'p':
                paused = not paused
                continue
            if paused:
                continue
            if command == 'n':
                if state.status == 'level_won':
                    try:
                        state.next_level()
                    except MazeError as exc:
                        print(f'Error: {exc}', file=sys.stderr)
                        return 1
                else:
                    print('Clear the current level before advancing.')
                continue
            if state.status != 'playing':
                continue
            if command == 'i':
                state.toggle_invisibility()
                continue  # Toggling the cheat does not consume time.
            if command in KEYS:
                state.set_direction(KEYS[command])
            elif command:
                print('Use WASD, Enter, I, P, N, or Q.')
                continue  # Invalid input does not advance simulation time.
            state.update(state.STEP_TIME)
    except MazeError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\nDemo closed.')
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
