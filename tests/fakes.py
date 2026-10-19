"""Test doubles: fake window, fake game state and fake highscores."""

from __future__ import annotations

from dataclasses import dataclass, field

from pacman.entities import Entity, Ghost, Grid, Position


@dataclass
class FakeState:
    """Minimal game state matching frontend.protocols.GameStateProtocol."""

    grid: Grid
    player: Entity
    ghosts: list[Ghost]
    pacgums: set[Position] = field(default_factory=set)
    super_pacgums: set[Position] = field(default_factory=set)
    score: int = 0
    lives: int = 3
    level: int = 1
    time_left: float = 90.0
    edible_timer: float = 0.0
    status: str = 'playing'
    invisible: bool = False


def open_grid(rows: int, cols: int) -> Grid:
    """Return a grid with a wall border and corridors inside."""

    return [
        [1 if row in (0, rows - 1) or col in (0, cols - 1) else 0
         for col in range(cols)]
        for row in range(rows)
    ]


def make_state(rows: int = 7, cols: int = 7) -> FakeState:
    """Build a level laid out like the real core.

    The player is in the middle, the ghosts and super-pacgums are in the
    four inner corners, and every other corridor tile has a pacgum.
    """

    grid = open_grid(rows, cols)
    middle = (rows // 2, cols // 2)
    corners = [(1, 1), (1, cols - 2), (rows - 2, 1), (rows - 2, cols - 2)]
    pacgums = {
        (row, col)
        for row in range(rows) for col in range(cols)
        if grid[row][col] == 0 and (row, col) not in {middle, *corners}
    }

    return FakeState(
        grid=grid,
        player=Entity(middle),
        ghosts=[Ghost(pos) for pos in corners],
        pacgums=pacgums,
        super_pacgums=set(corners),
    )
