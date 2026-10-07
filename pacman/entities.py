"""Directions and entities"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Position data type
Position = tuple[int, int]  # (row, column)


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
