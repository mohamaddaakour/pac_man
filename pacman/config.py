from __future__ import annotations
from typing import Any, Callable

from dataclasses import dataclass
import sys
import math
from pathlib import Path
import json


Report = Callable[[str], None]


class ConfigError(Exception):
    """The config file is missing, unreadable, or not a JSON object."""


@dataclass(frozen=True)
class LevelSpec:
    """Maze parameters of one level."""

    width: int
    height: int

    seed: int | None  # None means "pick a random seed."


@dataclass(frozen=True)
class Config:
    """Validated game settings."""
    highscore_filename: str
    levels: tuple[LevelSpec, ...]
    lives: int
    points_per_pacgum: int
    points_per_super_pacgum: int
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
    """Ignore comments while preserving strings and error locations.

    Support full-line ``#``, line ``//``, and block ``/* ... */`` comments.

    Raise:
        ConfigError if a block comment is not closed.
    """
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False
    line_has_only_whitespace = True

    while index < len(text):
        char = text[index]

        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        # Check if the starting block is also closed
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end == -1:
                raise ConfigError("Unclosed block comment in config file")
            for comment_char in text[index:end + 2]:
                if comment_char in "\r\n":
                    result.append(comment_char)
                    line_has_only_whitespace = True
                else:
                    result.append(" ")
            index = end + 2
            continue

        if text.startswith("//", index) or (
            char == "#" and line_has_only_whitespace
        ):
            while index < len(text) and text[index] not in "\r\n":
                result.append(" ")
                index += 1
            continue

        result.append(char)
        if char in "\r\n":
            line_has_only_whitespace = True
        elif not char.isspace():
            line_has_only_whitespace = False
        if char == '"':
            in_string = True
        index += 1

    return "".join(result)


def _read_number(
    raw: dict[str, Any],
    key: str,
    label: str,
    spec: tuple[bool, float, float, float],
    report: Report
) -> int | float:
    """
    Return `raw[key]` if validated against `spec`, or a safe fallback.

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
        ok_type: tuple[type[int] | type[float], ...] = (int,)
    else:
        ok_type = (int, float)

    # Check if the value is bool or not double or int
    if isinstance(value, bool) or not isinstance(value, ok_type):
        if is_int:
            wanted: str = "an integer"
        else:
            wanted = "a number"

        report(f"`{label}` must be {wanted}, but got {value!r}; "
               f"using default {fallback}")

        return fallback

    # Check if the value is not finite
    if isinstance(value, float) and not math.isfinite(value):
        report(f"`{label}` must be finite, but got {value!r}; "
               f"using default {fallback}")

        return fallback

    # Building `clamp`
    # If value is less than minimum `low` the value should take
    # `low` as value
    if value < low:
        report(f"`{label}` is {value}, below minimum; using {low:g}")
        value = low
    elif value > high:
        report(f"`{label}` is {value}, above maximum; using {high:g}")
        value = high

    if is_int:
        return int(value)
    else:
        return float(value)


# A seed is used to make randomness reproducible, this means
# same algorithm + same seed gives same maze.
def _read_seed(item: dict[str, Any], label: str, report: Report) -> int | None:
    """Return the seed of a level entry, or `None` for random seed"""

    seed: int | None = item.get("seed")

    if seed is None:
        return None

    if isinstance(seed, bool) or not isinstance(seed, int):
        report(f"`{label}.seed` must be an integer, but got {seed!r}; "
               f"now we will use a random seed")

        return None

    return seed


def _read_levels(raw: dict[str, Any], report: Report) -> tuple[LevelSpec, ...]:
    """Parse the `levels` list, invalid entries are skipped

    Args:
        raw: `LevelSpec` instance.
    """

    # Check if "levels" is a key in `raw`
    if "levels" not in raw:
        report("`levels` is missing, we will use the default level list")
        return DEFAULT_LEVELS

    value = raw["levels"]
    if not isinstance(value, list):
        report("`levels` must be a list; using the default level list")
        return DEFAULT_LEVELS

    size_spec = (True, DEFAULT_SIZE, MIN_SIZE, MAX_SIZE)

    levels: list[LevelSpec] = []

    for index, item in enumerate(value, start=1):
        label: str = f"level[{index}]"

        if not isinstance(item, dict):
            report(f"`{label}` must be an object, skipping it")
            continue

        # Report the unknown level keys
        # `set(item)` will create a set of dictonary keys
        for extra in sorted(set(item).difference(KNOWN_LEVEL_KEYS)):
            report(f"unknown key `{label}.{extra}` ignored")

        width: int = int(
            _read_number(item, "width", f"{label}.width", size_spec, report)
        )

        height: int = int(_read_number(item, "height", f"{label}.height",
                                       size_spec, report))

        levels.append(
            LevelSpec(width, height, _read_seed(item, label, report))
        )

    if not levels:
        report("`levels` has no usable entry, we will use default level list")

        return DEFAULT_LEVELS

    return tuple(levels)


def _read_filename(raw: dict[str, Any], report: Report) -> str:
    """Return the highscore filename, if it is unusable return the default
    highscore file name.
    """

    value: str | None = raw.get("highscore_filename")

    if value is None:
        report("`highscore_filename` is missing, we will use default filename "
               f"`{DEFAULT_HIGHSCORE_FILENAME}`")

        return DEFAULT_HIGHSCORE_FILENAME

    if not isinstance(value, str) or not value.strip():
        report(
            "`highscore_filename` must be a non-empty string, and got "
            f"{value!r}; we will use default `{DEFAULT_HIGHSCORE_FILENAME}`"
        )

        return DEFAULT_HIGHSCORE_FILENAME

    return value.strip()


def parse_config(
        raw: dict[str, Any], report: Report = _print_report
) -> Config:
    """Turn a JSON object into a validated `Config` instance."""

    # Ignore the unknown keys
    for key in sorted(set(raw).difference(KNOWN_KEYS)):
        report(f"Unknown key `{key}`, it will be ignored")

    numbers: dict[str, int | float] = {}

    for key, spec in NUMERIC_KEYS.items():
        numbers[key] = _read_number(raw, key, key, spec, report)

    return Config(
        highscore_filename=_read_filename(raw, report),
        levels=_read_levels(raw, report),
        lives=int(numbers["lives"]),
        points_per_pacgum=int(numbers["points_per_pacgum"]),
        points_per_super_pacgum=int(numbers["points_per_super_pacgum"]),
        points_per_ghost=int(numbers["points_per_ghost"]),
        level_max_time=float(numbers["level_max_time"]),
        edible_duration=float(numbers["edible_duration"]),
        ghost_respawn_time=float(numbers["ghost_respawn_time"]),
    )


def load_config(path: str | Path, report: Report = _print_report) -> Config:
    """Read and validate a config file.

    Raises:
        ConfigError: file missing/unreadable, not JSON, or not an object.
    """

    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {path}")
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"cannot read config file {path}: {exc}")

    try:
        raw = json.loads(_strip_comments(text))
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"{path} is not valid JSON (line {exc.lineno}, "
            f"column {exc.colno}): {exc.msg}")

    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: top level must be a JSON object")

    return parse_config(raw, report)
