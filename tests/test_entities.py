"""A3: directions, boundary checks, and center/corner spawn rules."""

import pytest

from pacman.entities import Direction, choose_spawns, is_walkable
from pacman.maze_adapter import MazeError
from tests.core_helpers import open_grid


def test_direction_vectors() -> None:
    """Directions change exactly one coordinate by one tile."""
    assert {(d.dr, d.dc) for d in Direction} == {
        (-1, 0), (1, 0), (0, -1), (0, 1),
    }


def test_walkability_rejects_walls_and_outside_positions() -> None:
    """Negative coordinates must not wrap around Python lists."""
    grid = open_grid()
    assert is_walkable(grid, (3, 3))
    for pos in ((0, 0), (-1, 3), (3, -1), (7, 3), (3, 7)):
        assert not is_walkable(grid, pos)
    assert not is_walkable([], (0, 0))


def test_center_and_four_corner_spawns() -> None:
    """Open rooms have the expected center and distinct corner spawns."""
    player, ghosts = choose_spawns(open_grid())
    assert player == (3, 3)
    assert ghosts == ((1, 1), (1, 5), (5, 1), (5, 5))


def test_blocked_center_uses_nearest_corridor() -> None:
    """A center wall produces a deterministic nearest-floor spawn."""
    grid = open_grid()
    grid[3][3] = 1
    player, ghosts = choose_spawns(grid)
    assert player == (2, 3)
    assert len(set((player, *ghosts))) == 5


@pytest.mark.parametrize('grid', [[], [[]], [[0], []], [[0, 0, 0, 0]]])
def test_invalid_or_tiny_maps_have_clear_errors(grid: list[list[int]]) -> None:
    """Insufficient or malformed maps cannot yield overlapping spawns."""
    with pytest.raises(MazeError):
        choose_spawns(grid)
