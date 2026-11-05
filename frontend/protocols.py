"""Interfaces the frontend reads: the game state and the highscores."""

from typing import Protocol
from collections.abc import Sequence
from pacman.entities import Direction, GhostState, Grid, Position


class EntityProtocol(Protocol):
    """A moving entity: its tile and its direction."""

    pos: Position
    direction: Direction | None


class GhostProtocol(EntityProtocol, Protocol):
    """An entity with a ghost state (normal, edible or eaten)."""

    state: GhostState


class GameStateProtocol(Protocol):
    """What the frontend reads from the game core.

    Every member is a read-only property, so mypy rejects any
    attempt by the frontend to change the game.
    """

    @property
    def grid(self) -> Grid:
        """Maze tiles: 0 for a corridor, 1 for a wall."""
        ...

    @property
    def player(self) -> EntityProtocol:
        """Pac-Man."""
        ...

    @property
    def ghosts(self) -> Sequence[GhostProtocol]:
        """The four ghosts, in spawn-corner order."""
        ...

    @property
    def pacgums(self) -> set[Position]:
        """Tiles that still have a pacgum."""
        ...

    @property
    def super_pacgums(self) -> set[Position]:
        """Tiles that still have a super-pacgum."""
        ...

    @property
    def score(self) -> int:
        """Current score."""
        ...

    @property
    def lives(self) -> int:
        """Lives left."""
        ...

    @property
    def level(self) -> int:
        """Current level, starting at 1."""
        ...

    @property
    def total_levels(self) -> int:
        """Total number of planned levels."""
        ...

    @property
    def time_left(self) -> float:
        """Seconds left to clear the level."""
        ...

    @property
    def edible_timer(self) -> float:
        """Seconds of edible ghosts left, 0 when off."""
        ...

    @property
    def status(self) -> str:
        """Playing, level_won, game_won or game_over."""
        ...

    @property
    def invisible(self) -> bool:
        """True while the invisibility cheat is on."""
        ...

    def update(self, dt: float) -> None:
        """Advance the game by `dt` seconds."""
        ...

    def set_direction(self, direction: Direction) -> None:
        """Ask Pac-Man to turn as soon as possible."""
        ...

    def toggle_invisibility(self) -> None:
        """Flip the invisibility cheat."""
        ...

    def skip_level(self) -> None:
        """Win the current level at once (cheat)."""
        ...

    def next_level(self) -> None:
        """Build the next level after a cleared one."""
        ...


class HighscoresProtocol(Protocol):
    """What the frontend uses from the highscore table."""

    last_error: str | None

    def load(self) -> None:
        """Read the table from disk."""
        ...

    def qualifies(self, score: int) -> bool:
        """Return True if `score` would enter the top 10."""
        ...

    def add(self, name: str, score: int) -> bool:
        """Add an entry and save; return True if it was added."""
        ...

    def top10(self) -> list[tuple[str, int]]:
        """Return the best entries as (name, score), best first."""
        ...
