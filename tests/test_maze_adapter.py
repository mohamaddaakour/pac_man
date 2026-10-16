"""Conversion and integration tests for the assigned maze package."""

from __future__ import annotations

import random
from unittest.mock import patch

import pytest

import pacman.maze_adapter as adapter
from pacman.entities import choose_spawns, is_walkable
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


@pytest.mark.parametrize('seed', range(1, 21))
def test_generated_maps_are_connected_with_valid_spawns(seed: int) -> None:
    """Twenty assigned-package outputs satisfy A2 and A3 acceptance."""
    grid = adapter.build_grid(9, 9, seed)
    assert len(grid) == len(grid[0]) == 19
    assert adapter.is_connected(grid)
    player, ghosts = choose_spawns(grid)
    assert len(set((player, *ghosts))) == 5
    assert all(is_walkable(grid, pos) for pos in (player, *ghosts))


def test_repeatable_generation_preserves_global_random_state() -> None:
    """The external package cannot perturb the application's random state."""
    before = random.getstate()
    first = adapter.build_grid(9, 9, 42)
    assert random.getstate() == before
    assert adapter.build_grid(9, 9, 42) == first
    assert random.getstate() == before


def test_generator_receives_nonperfect_option() -> None:
    """Use the assigned API as-is, explicitly disabling perfect mazes."""
    cells = adapter._generate_cells(9, 9, 42)
    with patch.object(adapter, 'MazeGenerator') as generator:
        generator.return_value.maze = cells
        adapter.build_grid(9, 9, 42)
        generator.assert_called_once_with(
            size=(9, 9), perfect=False, seed=42,
        )


def test_generation_failure_retries_then_reports_clear_error() -> None:
    """Generator exceptions are bounded and exposed as MazeError."""
    with patch.object(
        adapter, '_generate_cells', side_effect=RuntimeError('broken package'),
    ) as generate:
        with pytest.raises(MazeError, match='after 6 attempts: broken'):
            adapter.build_grid(9, 9, 42)
        assert generate.call_count == 6


def test_failed_attempt_can_recover() -> None:
    """A valid retry replaces the failed attempt instead of aborting."""
    cells = adapter._generate_cells(9, 9, 42)
    with patch.object(
        adapter, '_generate_cells', side_effect=[RuntimeError('retry'), cells],
    ) as generate:
        assert adapter.is_connected(adapter.build_grid(9, 9, 42))
        assert generate.call_count == 2
        assert generate.call_args_list[0] != generate.call_args_list[1]


def test_disconnected_output_is_retried_and_rejected() -> None:
    """A syntactically valid all-wall maze is not a playable map."""
    with patch.object(
        adapter, '_generate_cells', return_value=[[15] * 5 for _ in range(5)],
    ) as generate:
        with pytest.raises(MazeError, match='empty or disconnected'):
            adapter.build_grid(5, 5, None)
        assert generate.call_count == 6


@pytest.mark.parametrize('width,height', [(4, 5), (5, 100), (True, 5)])
def test_invalid_dimensions_fail_before_generation(
    width: int, height: int,
) -> None:
    """Reject unsafe dimensions before invoking the external dependency."""
    with patch.object(adapter, '_generate_cells') as generate:
        with pytest.raises(MazeError, match='Maze sides'):
            adapter.build_grid(width, height, 42)
        generate.assert_not_called()
