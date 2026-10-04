from __future__ import annotations
from typing import Callable

from dataclasses import dataclass
import sys


Report = Callable[[str], None]


class ConfigError(Exception):
    """The config file is missing, unreadable, or not a JSON object."""


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


NUMERIC_KEYS: dict[str, tuple[bool, float, float, float]] = {
    "lives": (True, 3, 1, 9),
    "points_per_pacgum": (True, 10, 0, 10_000),
    "points_per_super_pacgum": (True, 50, 0, 10_000),
    "points_per_ghost": (True, 200, 0, 10_000),
    "level_max_time": (False, 90.0, 10.0, 3600.0),
    "edible_duration": (False, 10.0, 1.0, 60.0),
    "ghost_respawn_time": (False, 5.0, 1.0, 60.0),
}

DEFAULT_HIGHSCORE_FILENAME = "highscores.json"
DEFAULT_LEVELS = (LevelSpec(width=15, height=15, seed=42),)
MIN_SIZE, MAX_SIZE, DEFAULT_SIZE = 5, 99, 15
KNOWN_KEYS = {"highscore_filename", "levels", *NUMERIC_KEYS}
KNOWN_LEVEL_KEYS = {"width", "height", "seed"}


def _print_report(message: str) -> None:
    print(f"[config] {message}", file=sys.stderr)


def _strip_comments(text: str) -> str:
    """Ignore comment lines (`#` or `//`)"""

    lines: list[str] = []

    for line in text.splitlines():
        stripped: str = line.lstrip()

        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        else:
            lines.append(line)

    return "\n".join(lines)