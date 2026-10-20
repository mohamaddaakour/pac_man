"""Tests for drawing the maze, dots and sprites (frontend.renderer)."""

from __future__ import annotations

from collections.abc import Iterator

import pygame
import pytest

from frontend.constants import (
    BACKGROUND_COLOR, CORRIDOR_COLOR, EDIBLE_BLINK_COLOR, EDIBLE_COLOR,
    EYES_COLOR, GHOST_COLORS, HUD_CHEAT_COLOR, HUD_COLUMN_WIDTH, HUD_HEIGHT,
    HUD_MARGIN, HUD_TEXT_COLOR, HUD_WARNING_COLOR, MAX_TILE, MOUTH_PERIOD,
    PACGUM_COLOR, PACMAN_COLOR, SUPER_PACGUM_COLOR, WALL_COLOR,
    WINDOW_HEIGHT, WINDOW_WIDTH,
)
from frontend.layout import Layout, compute_layout
from frontend.renderer import Renderer, hud_items
from frontend.window import Window
from pacman.entities import Direction, GhostState, Position
from pacman.game_state import GameState
from tests.core_helpers import make_config
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


def hud_column(column: int) -> set[tuple[int, ...]]:
    """Return every colour drawn in one HUD column (0 is the lives)."""

    left = HUD_MARGIN + column * HUD_COLUMN_WIDTH
    return {
        colour((x, y))
        for x in range(left, min(left + HUD_COLUMN_WIDTH, WINDOW_WIDTH))
        for y in range(HUD_HEIGHT)
    }


def test_hud_items_show_score_level_and_time() -> None:
    state = make_state()
    state.score, state.level, state.total_levels = 1230, 3, 12

    assert hud_items(state) == [
        ('SCORE 1230', HUD_TEXT_COLOR),
        ('LEVEL 3/12', HUD_TEXT_COLOR),
        ('TIME 90', HUD_TEXT_COLOR),
    ]


@pytest.mark.parametrize('left, shown, warning', [
    (90.0, 'TIME 90', False),
    (89.2, 'TIME 90', False),   # rounded up: 0 only at the real timeout
    (10.01, 'TIME 11', False),
    (10.0, 'TIME 10', True),
    (0.4, 'TIME 1', True),
    (0.0, 'TIME 0', True),
])
def test_hud_time_rounds_up_and_warns_at_ten_seconds(
    left: float, shown: str, warning: bool,
) -> None:
    state = make_state()
    state.time_left = left
    text, hud_colour = hud_items(state)[2]

    assert text == shown
    assert hud_colour == (HUD_WARNING_COLOR if warning else HUD_TEXT_COLOR)


def test_hud_shows_invisible_only_while_the_cheat_is_on() -> None:
    state = make_state()
    assert all(text != 'INVISIBLE' for text, _ in hud_items(state))

    state.invisible = True
    assert hud_items(state)[-1] == ('INVISIBLE', HUD_CHEAT_COLOR)


def test_hud_items_accept_the_real_game_state() -> None:
    state = GameState(make_config())

    assert hud_items(state)[1][0] == f'LEVEL 1/{state.total_levels}'
    assert state.total_levels >= 10


def test_hud_is_drawn_in_the_band(window: Window) -> None:
    state = make_state()
    state.invisible = True
    state.time_left = 5.0
    Renderer(window).draw(state, 0.0)

    assert PACMAN_COLOR in hud_column(0)          # life icon
    assert HUD_TEXT_COLOR in hud_column(1)        # score
    assert HUD_TEXT_COLOR in hud_column(2)        # level
    assert HUD_WARNING_COLOR in hud_column(3)     # time, 5 s left
    assert HUD_CHEAT_COLOR in hud_column(4)       # invisible


def test_hud_hides_invisible_and_warning_when_not_needed(
    window: Window,
) -> None:
    state = make_state()
    Renderer(window).draw(state, 0.0)

    assert HUD_WARNING_COLOR not in hud_column(3)
    assert hud_column(4) == {BACKGROUND_COLOR}
