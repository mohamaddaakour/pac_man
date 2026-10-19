"""Tests for tile size, offsets and coordinates (frontend.layout)."""

from __future__ import annotations

import pytest

from frontend.layout import Layout, compute_layout, to_pixels

AREA_WIDTH, AREA_HEIGHT, MAX_TILE = 1200, 840, 48


@pytest.mark.parametrize('rows, cols, tile', [
    (11, 11, 48),     # 5x5 maze: capped at MAX_TILE
    (31, 31, 27),     # 15x15 maze
    (31, 39, 27),     # 19x15 maze: not square
    (199, 199, 4),    # 99x99 maze: the largest the config allows
])
def test_maze_fits_and_is_centred(rows: int, cols: int, tile: int) -> None:
    layout = compute_layout(rows, cols, AREA_WIDTH, AREA_HEIGHT, MAX_TILE)

    assert layout.tile == tile
    right = AREA_WIDTH - (layout.offset_x + cols * layout.tile)
    bottom = AREA_HEIGHT - (layout.offset_y + rows * layout.tile)
    assert layout.offset_x >= 0 and layout.offset_y >= 0
    assert right >= 0 and bottom >= 0
    assert abs(layout.offset_x - right) <= 1
    assert abs(layout.offset_y - bottom) <= 1


def test_to_pixels_uses_col_for_x_and_row_for_y() -> None:
    layout = Layout(tile=10, offset_x=5, offset_y=7)

    assert to_pixels(layout, (2, 3)) == (5 + 3 * 10, 7 + 2 * 10)


@pytest.mark.parametrize('args', [
    (0, 5, 100, 100, 10), (5, 0, 100, 100, 10), (5, 5, 0, 100, 10),
    (5, 5, 100, -1, 10), (5, 5, 100, 100, 0),
])
def test_non_positive_parameters_are_refused(
    args: tuple[int, int, int, int, int],
) -> None:
    with pytest.raises(ValueError, match='strictly positive'):
        compute_layout(*args)


def test_maze_too_large_for_area_is_refused() -> None:
    with pytest.raises(ValueError, match='cannot fit'):
        compute_layout(1000, 1000, 500, 500, 48)
