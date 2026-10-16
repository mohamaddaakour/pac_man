"""Tests for drawing the maze, dots and sprites (frontend.renderer)."""

from __future__ import annotations

from collections.abc import Iterator

import pygame
import pytest

from frontend.constants import (
    BACKGROUND_COLOR, CORRIDOR_COLOR, EDIBLE_BLINK_COLOR, EDIBLE_COLOR,
    EYES_COLOR, GHOST_COLORS, HUD_HEIGHT, MAX_TILE, MOUTH_PERIOD,
    PACGUM_COLOR, PACMAN_COLOR, SUPER_PACGUM_COLOR, WALL_COLOR,
    WINDOW_HEIGHT, WINDOW_WIDTH,
)
from frontend.layout import Layout, compute_layout
from frontend.renderer import Renderer
from frontend.window import Window
from pacman.entities import Direction, GhostState, Position
from tests.fakes import FakeState, make_state, open_grid

Pixel = tuple[int, int]


@pytest.fixture
def window() -> Iterator[Window]:
    """Open a headless window of the real game size."""

    win = Window(WINDOW_WIDTH, WINDOW_HEIGHT, 'test', headless_ok=True)
    yield win
    pygame.quit()


def layout_of(state: FakeState) -> Layout:
    """Return where the renderer must draw this maze in the window."""

    area = compute_layout(
        len(state.grid), len(state.grid[0]),
        WINDOW_WIDTH, WINDOW_HEIGHT - HUD_HEIGHT, MAX_TILE,
    )
    return Layout(area.tile, area.offset_x, area.offset_y + HUD_HEIGHT)


def centre(layout: Layout, pos: Position) -> Pixel:
    """Return the window pixel in the middle of a maze tile."""

    row, col = pos
    return (layout.offset_x + col * layout.tile + layout.tile // 2,
            layout.offset_y + row * layout.tile + layout.tile // 2)


def colour(pixel: Pixel) -> tuple[int, ...]:
    """Return the colour of a window pixel."""

    surface = pygame.display.get_surface()
    assert surface is not None
    return tuple(surface.get_at(pixel))[:3]


def drawn(window: Window, state: FakeState) -> Layout:
    """Draw one frame with a new renderer and return the layout used."""

    Renderer(window).draw(state, 0.0)
    return layout_of(state)


def test_walls_corridors_and_hud_band(window: Window) -> None:
    state = make_state()
    state.pacgums.discard((3, 1))
    layout = drawn(window, state)

    assert colour(centre(layout, (0, 0))) == WALL_COLOR
    assert colour(centre(layout, (3, 1))) == CORRIDOR_COLOR
    assert colour((5, 5)) == BACKGROUND_COLOR


@pytest.mark.parametrize('rows, cols', [
    (11, 11), (31, 31), (31, 39), (199, 199),
])
def test_every_maze_size_fits_below_the_hud(
    window: Window, rows: int, cols: int,
) -> None:
    state = make_state(rows, cols)
    layout = drawn(window, state)
    last = (rows - 1, cols - 1)

    assert layout.offset_y >= HUD_HEIGHT
    assert colour(centre(layout, (0, 0))) == WALL_COLOR
    assert colour(centre(layout, last)) == WALL_COLOR
    assert colour((layout.offset_x - 1, layout.offset_y)) == BACKGROUND_COLOR


def test_dots_are_erased_when_eaten_and_redrawn_when_back(
    window: Window,
) -> None:
    state = make_state()
    dot = (3, 1)
    renderer = Renderer(window)

    renderer.draw(state, 0.0)
    layout = layout_of(state)
    assert colour(centre(layout, dot)) == PACGUM_COLOR

    state.pacgums.discard(dot)
    renderer.draw(state, 0.0)
    assert colour(centre(layout, dot)) == CORRIDOR_COLOR

    state.pacgums.add(dot)
    renderer.draw(state, 0.0)
    assert colour(centre(layout, dot)) == PACGUM_COLOR


def test_super_pacgum_is_drawn_and_erased(window: Window) -> None:
    state = make_state()
    corner = state.ghosts[0].pos
    state.ghosts[0].pos = (1, 2)     # move the ghost off its super-pacgum
    state.pacgums.discard((1, 2))
    renderer = Renderer(window)

    renderer.draw(state, 0.0)
    layout = layout_of(state)
    assert colour(centre(layout, corner)) == SUPER_PACGUM_COLOR

    state.super_pacgums.discard(corner)
    renderer.draw(state, 0.0)
    assert colour(centre(layout, corner)) == CORRIDOR_COLOR


def test_each_ghost_has_its_own_colour(window: Window) -> None:
    state = make_state()
    layout = drawn(window, state)

    for ghost, expected in zip(state.ghosts, GHOST_COLORS):
        assert colour(centre(layout, ghost.pos)) == expected


def test_edible_ghost_is_blue_then_blinks_near_the_end(window: Window) -> None:
    state = make_state()
    state.ghosts[0].state = GhostState.EDIBLE
    renderer = Renderer(window)
    layout = layout_of(state)
    middle = centre(layout, state.ghosts[0].pos)

    state.edible_timer = 5.0
    renderer.draw(state, 0.0)
    assert colour(middle) == EDIBLE_COLOR

    seen = set()
    for left in (1.9, 1.7, 1.5, 1.3):
        state.edible_timer = left
        renderer.draw(state, 0.0)
        seen.add(colour(middle))
    assert seen == {EDIBLE_COLOR, EDIBLE_BLINK_COLOR}


def test_eaten_ghost_shows_only_its_eyes(window: Window) -> None:
    state = make_state()
    ghost = state.ghosts[0]
    ghost.state = GhostState.EATEN
    layout = drawn(window, state)
    left = layout.offset_x + ghost.pos[1] * layout.tile
    top = layout.offset_y + ghost.pos[0] * layout.tile
    tile = [colour((left + x, top + y))
            for x in range(layout.tile) for y in range(layout.tile)]

    assert GHOST_COLORS[0] not in tile
    assert EYES_COLOR in tile


def test_pacman_is_drawn_and_keeps_facing_when_stopped(
    window: Window,
) -> None:
    state = make_state()
    renderer = Renderer(window)
    layout = layout_of(state)
    x, y = centre(layout, state.player.pos)
    quarter = layout.tile // 3

    state.player.direction = Direction.UP
    renderer.draw(state, 0.0)
    state.player.direction = None
    renderer.draw(state, 0.0)

    assert colour((x, y + quarter)) == PACMAN_COLOR      # back of the head
    assert colour((x, y - quarter)) != PACMAN_COLOR      # open mouth, up


def test_mouth_chomps_only_while_moving(window: Window) -> None:
    state = make_state()
    renderer = Renderer(window)
    layout = layout_of(state)
    x, y = centre(layout, state.player.pos)
    in_mouth = (x + layout.tile // 3, y)
    state.player.direction = Direction.RIGHT

    shapes = []
    for dt in (MOUTH_PERIOD / 2, MOUTH_PERIOD, MOUTH_PERIOD):
        renderer.draw(state, dt)
        shapes.append(colour(in_mouth) == PACMAN_COLOR)
    assert shapes == [False, True, False]     # open, closed, open

    state.player.direction = None
    for _ in range(3):
        renderer.draw(state, MOUTH_PERIOD)
        assert colour(in_mouth) != PACMAN_COLOR   # stays open


def test_draw_creates_no_images(
    window: Window, monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = make_state(15, 15)
    renderer = Renderer(window)
    renderer.draw(state, 0.0)
    calls: list[tuple[int, int, bool]] = []
    real = window.new_image

    def counting(width: int, height: int, opaque: bool) -> object:
        calls.append((width, height, opaque))
        return real(width, height, opaque)

    monkeypatch.setattr(window, 'new_image', counting)
    for _ in range(50):
        state.pacgums.discard(next(iter(state.pacgums)))
        renderer.draw(state, 0.016)

    assert calls == []


def test_new_grid_rebuilds_the_level(window: Window) -> None:
    state = make_state(7, 7)
    renderer = Renderer(window)
    renderer.draw(state, 0.0)

    state.grid = open_grid(15, 21)
    state.pacgums = set()
    renderer.draw(state, 0.0)
    layout = layout_of(state)

    assert colour(centre(layout, (14, 20))) == WALL_COLOR
    assert colour(centre(layout, (7, 10))) == CORRIDOR_COLOR
