from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelSpec:
    """Maze parameters of one level."""

    width: int
    height: int

    seed: int | None # None means "pick a random seed."


@dataclass(frozen=True)
class Config:
    """Validated game settings."""
    highscore_filename: str
    levels: tuple[LevelSpec, ...]
    lives: int
    points_per_pacgum: int
    point_per_super_pacgum: int
    points_per_ghost: int
    level_max_time: float
    edible_duration: float
    ghost_respawn_time: float