from __future__ import annotations
from typing import Any, Callable

from dataclasses import dataclass
import sys
import math


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


def _read_number(
    raw: dict[str, Any],
    key: str,
    label: str,
    spec: tuple[bool, float, float, float],
    report: Report
) -> int | float:
    """
    Return `raw[key]` if validated against `spec`, otherwise return a safe fallback.

    Args:
        raw: Dict that may contain `key`
        key: Key to look up
        label: Name shown in messages
        spec: `(is_int, default, minimum, max)`
        report: called with one message per fix.
    
    Returns:
        `raw[key]` if validated otherwise return a fallback.
    """


    is_int, default, low, high = spec

    if is_int:
        fallback: int | float = int(default)
    else:
        fallback = float(default)

    if key not in raw:
        report(f"`{label}` is missing, using instead {fallback}")
        return fallback

    value = raw[key]

    if is_int:
        ok_type = (int,)
    else:
        ok_type = (int, float)
    
    # Check if the value is bool or not double or int
    if isinstance(value, bool) or not isinstance(value, ok_type):
        if is_int:
            wanted: str = "an integer"
        else:
            wanted: str = "a number"
    
        report(f"`{label}` must be {wanted}, but got {value!r}; "
           f"using default {fallback}")
        
        return fallback
    
    # Check if the value is not finite
    if not math.isfinite(value):
        report(f"`{label}` must be finite, but got {value!r}; "
               f"using default {fallback}")
        
        return fallback
    
    # Building `clamp`
    # If value is less than minimum `low` the value should take
    # `low` as value
    if value < low:
        report(f"`{label}` is {value}, below minimum; using {low:q}")
        value = low
    elif value > high:
        report(f"`{label}` is {value}, above maximum; using {high:q}")
        value = high
    
    if is_int:
        return int(value)
    else:
        return float(value)