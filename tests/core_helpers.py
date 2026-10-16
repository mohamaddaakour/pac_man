"""Small deterministic inputs for core behavior tests."""

from dataclasses import replace

from pacman.config import Config, DEFAULT_LEVELS, LevelSpec, parse_config
from pacman.game_state import GameState
from pacman.entities import GhostState, Grid


def make_config(
    *, levels: tuple[LevelSpec, ...] = DEFAULT_LEVELS,
    level_max_time: float = 90.0,
    highscore_filename: str = 'highscores.json',
) -> Config:
    """Return normal defaults with explicit changes for a scenario."""
    return replace(
        parse_config({}, lambda message: None), levels=levels,
        level_max_time=level_max_time, highscore_filename=highscore_filename,
    )


def open_grid() -> Grid:
    """Return five by five open floor tiles inside a wall boundary."""
    return [
        [int(row in (0, 6) or col in (0, 6)) for col in range(7)]
        for row in range(7)
    ]


def park_ghosts(state: GameState) -> None:
    """Keep ghosts inactive while a test isolates player movement."""
    for ghost in state.ghosts:
        ghost.state = GhostState.EATEN
        ghost.respawn_timer = 1000.0
