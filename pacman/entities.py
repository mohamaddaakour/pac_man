"""Directions and entitie."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pacman.maze_adapter import MazeError

# Position data type
Position = tuple[int, int]  # (row, column)
Grid = list[list[int]]


class Direction(Enum):
    """Four move directions"""

    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

    # Used to calculate the new position
    # example: next_pos = (row + d.dr, col + d.dc)
    @property
    def dr(self) -> int:
        """Row delta."""
        return self.value[0]

    @property
    def dc(self) -> int:
        """Column delta."""
        return self.value[1]


@dataclass
class Entity:
    pos: Position
    direction: Direction | None = None


def is_walkable(grid: Grid, pos: Position) -> bool:
    """Check if the position is walkable or not"""

    row, col = pos

    return (
        0 <= row < len(grid)
        and 0 <= col < len(grid[row])
        and grid[row][col] == 0
    )


def choose_spawns(
    grid: Grid,
) -> tuple[Position, tuple[Position, ...]]:
    """Pick a center player and distinct TL, TR, BL, BR ghost positions."""

    if (
        not grid
        or not grid[0]
        or any(len(row) != len(grid[0]) for row in grid)
    ):
        raise MazeError(
            "Spawn selection requires a rectangular grid"
        )

    rows = len(grid)
    cols = len(grid[0])

    available = {
        (row, col)
        for row in range(rows)
        for col in range(cols)
        if is_walkable(grid, (row, col))
    }

    if len(available) < 5:
        raise MazeError(
            "Need five corridor tiles for distinct spawns"
        )

    def take_nearest(target: Position) -> Position:
        """Choose by Manhattan distance, then row/column, and reserve."""

        chosen = min(
            available,
            key=lambda pos: (
                abs(pos[0] - target[0])
                + abs(pos[1] - target[1]),
                pos,
            ),
        )

        available.remove(chosen)
        return chosen

    # Player closest to center.
    player = take_nearest(
        (rows // 2, cols // 2)
    )

    # Ghosts: TL, TR, BL, BR.
    corners = (
        (0, 0),
        (0, cols - 1),
        (rows - 1, 0),
        (rows - 1, cols - 1),
    )

    ghosts = tuple(
        take_nearest(corner)
        for corner in corners
    )

    return player, ghosts