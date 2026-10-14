"""Play the campaign with line-based terminal input."""

from __future__ import annotations

import sys

from pacman.config import Config, ConfigError, load_config
from pacman.entities import Direction, GhostState
from pacman.game_state import GameState
from pacman.highscore import Highscores
from tools.session import load_highscores, score_lines
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


def play_campaign(config: Config) -> GameState | None:
    """Play until a final result; unfinished games submit no score."""
    state = GameState(config)
    paused = False
    print('WASD/Enter: move   I: invisible   P: pause   N: next   Q: menu')
    while True:
        print(render_ascii(state))
        remaining = len(state.pacgums) + len(state.super_pacgums)
        print(
            f'Level: {state.level}/{len(state.levels)} | '
            f'Time: {state.time_left:.1f}s | Score: {state.score} | '
            f'Lives: {state.lives} | Pellets: {remaining} | '
            f'Invisible: {state.invisible} | '
            f'Power: {state.edible_timer:.1f}s | '
            f'Grace: {state.grace_timer:.1f}s'
        )
        if state.status in ('game_won', 'game_over'):
            outcome = ('Campaign won!' if state.status == 'game_won'
                       else 'Game over!')
            print(f'{outcome} Final score: {state.score}')
            return state
        if state.status == 'level_won':
            print('Level complete! N advances; Q returns to the menu.')
        if paused:
            print('Paused — P resumes, Q returns to menu.')
        command = input('Command: ').strip().lower()
        if command == 'q':
            return None
        if command == 'p':
            paused = not paused
            continue
        if paused:
            continue
        if command == 'n':
            if state.status == 'level_won':
                state.next_level()
            else:
                print('Clear the current level before advancing.')
            continue
        if state.status != 'playing':
            continue
        if command == 'i':
            state.toggle_invisibility()
            continue
        if command in KEYS:
            state.set_direction(KEYS[command])
        elif command:
            print('Use WASD, Enter, I, P, N, or Q.')
            continue
        state.update(state.STEP_TIME)


def submit_score(scores: Highscores, score: int) -> None:
    """Offer one submission; invalid names can be corrected or skipped."""
    if not scores.qualifies(score):
        print('This score does not enter the top ten.')
        return
    while True:
        name = input('Name (1–10 letters/digits/spaces; Enter skips): ')
        if not name:
            return
        if scores.add(name, score):
            print('Score saved.')
            return
        print(scores.last_error or 'Could not save the score.')


def main(argv: list[str]) -> int:
    """Run menu, campaign, name entry, and persistent score table."""
    if len(argv) > 2:
        print('Usage: python -m tools.cli_demo [config.json]', file=sys.stderr)
        return 1
    path = argv[1] if len(argv) > 1 else 'config.json'
    try:
        config = load_config(path)
        scores = load_highscores(config, path)
        while True:
            print('\nPac-Man: S=start   H=scores   T=help   Q=quit')
            choice = input('Menu: ').strip().lower()
            if choice == 'q':
                return 0
            if choice in ('s', ''):
                completed = play_campaign(config)
                if completed is not None:
                    submit_score(scores, completed.score)
                    print('\n'.join(score_lines(scores)))
            elif choice == 'h':
                print('\n'.join(score_lines(scores)))
            elif choice == 't':
                print('WASD + Enter moves; Enter continues. I protects you.')
                print('P: pause; N: next cleared level; Q: menu.')
                print('Collect pellets; ghosts and timeouts cost lives.')
                print('Power makes ghosts edible. Clear all levels to win.')
            else:
                print('Use S, H, T, or Q.')
    except (EOFError, KeyboardInterrupt):
        print('\nClosed.')
        return 0
    except (ConfigError, MazeError, OSError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    except Exception as exc:
        # Final application boundary: unexpected failures still exit clearly.
        print(f'Unexpected game error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
