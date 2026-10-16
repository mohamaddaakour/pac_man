"""A6: distance maps, chase/flee decisions, and reversal constraints."""

import random
from unittest.mock import patch

from pacman.entities import Direction, Ghost, GhostState
from pacman.ghost_ai import choose_direction, distance_map
from tests.core_helpers import open_grid


def test_bfs_distances_and_invalid_goal() -> None:
    """Open-room distances equal Manhattan distances and exclude walls."""
    grid = open_grid()
    distances = distance_map(grid, (3, 3))
    assert len(distances) == 25
    assert distances[(1, 1)] == 4
    assert (0, 0) not in distances
    assert distance_map(grid, (0, 0)) == {}


def test_chasing_ghost_reaches_player() -> None:
    """Repeated best moves reach the target on an open grid."""
    grid = open_grid()
    ghost = Ghost((1, 1))
    goal = (5, 5)
    distances = distance_map(grid, goal)
    rng = random.Random(0)
    with patch.object(rng, 'random', return_value=0.0):
        for _ in range(8):
            direction = choose_direction(grid, ghost, distances, rng)
            assert direction is not None
            row, col = ghost.pos
            ghost.pos = row + direction.dr, col + direction.dc
            ghost.direction = direction
    assert ghost.pos == goal
    assert choose_direction(grid, ghost, distances, rng) is None


def test_edible_ghost_moves_farther_from_player() -> None:
    """A fleeing ghost chooses the greatest reachable BFS distance."""
    grid = open_grid()
    distances = distance_map(grid, (3, 1))
    ghost = Ghost((3, 3), state=GhostState.EDIBLE)
    direction = choose_direction(grid, ghost, distances, random.Random(0))
    assert direction is not None
    target = (3 + direction.dr, 3 + direction.dc)
    assert distances[target] > distances[ghost.pos]


def test_junction_probability_threshold_and_random_branch() -> None:
    """Choose the best branch below .70, and a random branch at .70."""
    grid = open_grid()
    distances = distance_map(grid, (3, 5))
    ghost = Ghost((3, 3))
    rng = random.Random(0)
    with patch.object(rng, 'random', return_value=0.699):
        direction = choose_direction(grid, ghost, distances, rng)
        assert direction == Direction.RIGHT
    with patch.object(rng, 'random', return_value=0.70):
        with patch.object(rng, 'choice', return_value=Direction.UP) as choice:
            direction = choose_direction(grid, ghost, distances, rng)
            assert direction == Direction.UP
            choice.assert_called_once()


def test_no_reversal_except_at_dead_end() -> None:
    """A closer player behind the ghost does not permit an immediate U-turn."""
    grid = open_grid()
    ghost = Ghost((3, 3), Direction.RIGHT)
    distances = distance_map(grid, (3, 1))
    for seed in range(20):
        assert choose_direction(
            grid, ghost, distances, random.Random(seed)
        ) != Direction.LEFT
    grid = [[1] * 5, [1, 0, 0, 0, 1], [1] * 5]
    ghost = Ghost((1, 3), Direction.RIGHT)
    assert choose_direction(
        grid, ghost, distance_map(grid, (1, 1)), random.Random(0)
    ) == Direction.LEFT


def test_eaten_and_unreachable_ghosts_do_not_move() -> None:
    """Inactive ghosts never request a direction."""
    grid = open_grid()
    ghost = Ghost((1, 1), state=GhostState.EATEN)
    assert choose_direction(
        grid, ghost, distance_map(grid, (3, 3)), random.Random(0)
    ) is None
    ghost.state = GhostState.NORMAL
    assert choose_direction(grid, ghost, {}, random.Random(0)) is None
