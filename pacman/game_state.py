from __future__ import annotations

from pacman.entities import Direction
from pacman.config import Config


class GameState:
    """All mutable state of a running game."""

    status: str  # "playing" | "level_won" | "game_won" | "game_over"

    score: int
    lives: int

    level: int  # 1-based

    time_left: float
    invisible: bool

    def __init__(self, config: Config) -> None:
        raise NotImplementedError

    def update(self, dt: float) -> None:
        raise NotImplementedError

    def set_direction(self, direction: Direction) -> None:
        raise NotImplementedError

    def toggle_invisibility(self) -> None:
        """Flip the cheat mode flag."""
        raise NotImplementedError

    def next_level(self) -> None:
        """Build the next level, keeping score and lives."""
        raise NotImplementedError
