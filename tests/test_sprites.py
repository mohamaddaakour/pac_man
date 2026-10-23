"""Tests for sprite pixel data (frontend.sprites)."""

from __future__ import annotations

import pytest

from frontend.constants import EYES_COLOR, PACMAN_COLOR
from frontend.sprites import disc, eyes, ghost, pacman, scale_up
from pacman.entities import Direction

RED = (255, 0, 0)


def alpha(pixels: bytes, size: int, x: int, y: int) -> int:
    """Return the alpha byte of pixel (x, y)."""

    return pixels[(y * size + x) * 4 + 3]


def rgb(pixels: bytes, size: int, x: int, y: int) -> tuple[int, ...]:
    """Return the colour of pixel (x, y)."""

    start = (y * size + x) * 4
    return tuple(pixels[start:start + 3])


def mask(pixels: bytes, size: int) -> list[str]:
    """Return the sprite as rows of '#' (opaque) and '.' (transparent)."""

    return [
        ''.join('#' if alpha(pixels, size, x, y) else '.'
                for x in range(size))
        for y in range(size)
    ]


@pytest.mark.parametrize('size', [4, 5, 12, 27, 48])
def test_every_sprite_has_one_rgba_pixel_per_tile_pixel(size: int) -> None:
    for pixels in (disc(size, size / 3, RED), ghost(size, RED), eyes(size),
                   pacman(size, Direction.RIGHT, True)):
        assert len(pixels) == size * size * 4


@pytest.mark.parametrize('size', [4, 5, 12, 27, 48])
def test_every_sprite_stays_visible_on_small_tiles(size: int) -> None:
    for pixels in (disc(size, size / 8, RED), ghost(size, RED), eyes(size),
                   pacman(size, Direction.RIGHT, True)):
        assert any(alpha(pixels, size, x, y)
                   for x in range(size) for y in range(size))


def test_disc_is_opaque_in_the_middle_and_clear_in_the_corners() -> None:
    pixels = disc(12, 4, RED)

    assert rgb(pixels, 12, 6, 6) == RED
    assert alpha(pixels, 12, 6, 6) == 255
    assert alpha(pixels, 12, 0, 0) == 0
    assert alpha(pixels, 12, 11, 11) == 0


@pytest.mark.parametrize('direction, mouth, back', [
    (Direction.RIGHT, (12, 7), (2, 7)),
    (Direction.LEFT, (2, 7), (12, 7)),
    (Direction.UP, (7, 2), (7, 12)),
    (Direction.DOWN, (7, 12), (7, 2)),
])
def test_pacman_mouth_faces_its_direction(
    direction: Direction, mouth: tuple[int, int], back: tuple[int, int],
) -> None:
    opened = pacman(15, direction, True)
    closed = pacman(15, direction, False)

    assert alpha(opened, 15, *mouth) == 0
    assert alpha(opened, 15, *back) == 255
    assert rgb(opened, 15, *back) == PACMAN_COLOR
    assert alpha(closed, 15, *mouth) == 255


@pytest.mark.parametrize('sprite', ['ghost', 'eyes', 'pacman'])
def test_sprites_are_left_right_symmetric(sprite: str) -> None:
    pixels = {
        'ghost': ghost(12, RED),
        'eyes': eyes(12),
        'pacman': pacman(12, Direction.UP, True),
    }[sprite]

    assert all(row == row[::-1] for row in mask(pixels, 12))


def test_ghost_has_a_rounded_top_and_uses_its_colour() -> None:
    pixels = ghost(12, RED)

    assert alpha(pixels, 12, 0, 0) == 0
    assert alpha(pixels, 12, 11, 0) == 0
    assert rgb(pixels, 12, 6, 6) == RED


def test_eyes_are_two_separate_eyes_in_eyes_colour() -> None:
    pixels = eyes(12)
    middle_row = mask(pixels, 12)[5]

    assert middle_row.count('#') >= 2
    assert '.#' in middle_row and '#.' in middle_row
    assert middle_row[5:7] == '..'
    x = middle_row.index('#')
    assert rgb(pixels, 12, x, 5) == EYES_COLOR


def test_scale_up_turns_each_pixel_into_a_block() -> None:
    red, blue = bytes((255, 0, 0, 255)), bytes((0, 0, 255, 255))
    big = scale_up(red + blue, 2, 1, 2)       # 2x1 image, twice as big

    assert big == (red * 2 + blue * 2) * 2    # two identical 4-pixel rows


@pytest.mark.parametrize('factor', [1, 3])
def test_scale_up_keeps_every_byte_in_place(factor: int) -> None:
    pixels = bytes(range(2 * 3 * 4))          # 2x3 image, all bytes differ
    big = scale_up(pixels, 2, 3, factor)

    assert len(big) == 2 * 3 * factor * factor * 4
    for y in range(3 * factor):
        for x in range(2 * factor):
            source = ((y // factor) * 2 + x // factor) * 4
            target = (y * 2 * factor + x) * 4
            assert big[target:target + 4] == pixels[source:source + 4]
