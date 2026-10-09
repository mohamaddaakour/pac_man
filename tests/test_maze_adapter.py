"""Conversion and integration tests for the assigned maze package."""

from __future__ import annotations

# import random

import pytest

# import pacman.maze_adapter as adapter
# from pacman.entities import choose_spawns, is_walkable
from pacman.maze_adapter import (
    MazeError,
    _convert_cells,
)


def test_horizontal_passage_and_blocked_cell() -> None:
    """13 opens east, 7 opens west, and 15 stays fully blocked."""

    assert _convert_cells(
        [[13, 7, 15]],
        3,
        1,
    ) == [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ]


def test_vertical_passage() -> None:
    assert _convert_cells(
        [[11], [14]],
        1,
        2,
    ) == [
        [1, 1, 1],
        [1, 0, 1],
        [1, 0, 1],
        [1, 0, 1],
        [1, 1, 1],
    ]


@pytest.mark.parametrize(
    'cells',
    [
        None,
        [],
        [[15]],
        [[15, 15], [15]],
        [[True, 15], [15, 15]],
        [[16, 15], [15, 15]],
        [[-1, 15], [15, 15]],
        [[1.0, 15], [15, 15]],
        [[13, 15], [15, 15]],
        [[14, 15], [15, 15]],
    ],
)
def test_bad_masks_are_rejected(
    cells: object,
) -> None:
    with pytest.raises(MazeError):
        _convert_cells(cells, 2, 2)
