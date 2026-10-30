"""End-to-end tests: the graphical app driving the real core and score file."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pygame
import pytest

from frontend.app import App, Mode
from frontend.constants import (
    HUD_HEIGHT, MAX_TILE, TRANSITION_TIME, WALL_COLOR, WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from frontend.layout import compute_layout
from frontend.window import KEY_ENTER, KEY_I, KEY_K, KEY_P, KeyEvent, Window
from pacman.config import Config, LevelSpec
from pacman.highscore import Highscores
from tests.core_helpers import make_config

ENTER = KeyEvent(KEY_ENTER, 0, '\r')
INVISIBLE = KeyEvent(KEY_I, 0, 'i')
PAUSE = KeyEvent(KEY_P, 0, 'p')
SKIP = KeyEvent(KEY_K, 0, 'k')


@pytest.fixture
def window() -> Iterator[Window]:
    """Open a headless window of the real game size."""

    win = Window(WINDOW_WIDTH, WINDOW_HEIGHT, 'test', headless_ok=True)
    yield win
    pygame.quit()


def scores_in(tmp_path: Path) -> Highscores:
    """Load the real score table stored in `tmp_path`."""

    table = Highscores(str(tmp_path / 'scores.json'))
    table.load()
    return table


def run_for(app: App, seconds: float) -> None:
    """Run frames at 60 per second for about `seconds`."""

    for _ in range(int(seconds * 60) + 1):
        app.on_frame(1 / 60)


def mode(app: App) -> Mode:
    """Read the current mode (a call, so mypy does not freeze its value)."""

    return app.mode


def started(window: Window, config: Config, table: Highscores) -> App:
    """Return an app playing level 1 of a real game."""

    app = App(window, config, table)
    app.on_frame(1 / 60)
    app.on_key(ENTER)
    run_for(app, TRANSITION_TIME + 0.1)
    assert mode(app) == Mode.PLAYING
    return app


def lose_by_timeout(window: Window, config: Config, table: Highscores) -> App:
    """Play with ghosts made harmless until the timer takes every life."""

    app = started(window, replace(config, level_max_time=10.0), table)
    app.on_key(INVISIBLE)
    for _ in range(1000):                      # 100 s at the capped dt
        if mode(app) == Mode.GAME_END:
            break
        app.on_frame(0.1)
    assert mode(app) == Mode.GAME_END
    assert not app.won
    return app


def submit_name(app: App, name: str) -> None:
    """Type a name on the end screen and press Enter."""

    for char in name:
        app.on_key(KeyEvent(0, 0, char))
    app.on_key(ENTER)


def test_skipping_every_level_reaches_the_victory_screen(
    window: Window, tmp_path: Path,
) -> None:
    app = started(window, make_config(), scores_in(tmp_path))
    assert app.state is not None
    total = app.state.total_levels
    levels: list[int] = []

    while mode(app) != Mode.GAME_END and len(levels) <= total:
        assert app.state is not None
        levels.append(app.state.level)
        app.on_key(SKIP)
        app.on_frame(1 / 60)                   # the core changes level
        run_for(app, TRANSITION_TIME + 0.1)

    assert levels == list(range(1, total + 1))
    assert total >= 10
    assert app.won


def test_each_new_level_is_drawn_at_its_own_size(
    window: Window, tmp_path: Path,
) -> None:
    app = started(window, make_config(), scores_in(tmp_path))
    assert app.state is not None
    first = app.state.grid
    app.on_key(SKIP)
    app.on_frame(1 / 60)                       # first transition frame
    grid = app.state.grid
    rows, cols = len(grid), len(grid[0])
    area = compute_layout(rows, cols, WINDOW_WIDTH,
                          WINDOW_HEIGHT - HUD_HEIGHT, MAX_TILE)
    corner = (area.offset_x + (cols - 1) * area.tile + area.tile // 2,
              area.offset_y + HUD_HEIGHT + (rows - 1) * area.tile
              + area.tile // 2)
    surface = pygame.display.get_surface()
    assert surface is not None

    assert rows > len(first)                   # later levels grow
    assert tuple(surface.get_at(corner))[:3] == WALL_COLOR


def test_pause_freezes_the_real_timer(window: Window, tmp_path: Path) -> None:
    app = started(window, make_config(), scores_in(tmp_path))
    assert app.state is not None
    run_for(app, 1.0)
    app.on_key(PAUSE)
    frozen = app.state.time_left

    run_for(app, 5.0)
    assert app.state.time_left == frozen

    app.on_key(PAUSE)
    run_for(app, 1.0)
    assert app.state.time_left < frozen


def test_name_after_game_over_is_saved_to_the_score_file(
    window: Window, tmp_path: Path,
) -> None:
    app = lose_by_timeout(window, make_config(), scores_in(tmp_path))

    submit_name(app, 'GM')

    assert mode(app) == Mode.MENU
    assert app.message == 'Highscore saved!'
    assert scores_in(tmp_path).top10() == [('GM', app.final_score)]


def test_full_table_still_asks_a_name_but_keeps_the_file(
    window: Window, tmp_path: Path,
) -> None:
    table = scores_in(tmp_path)
    for rank in range(10):
        assert table.add(f'PLAYER{rank}', 10_000 + rank)
    saved = (tmp_path / 'scores.json').read_text(encoding='utf-8')
    app = lose_by_timeout(window, make_config(), table)

    assert not app.can_save
    submit_name(app, 'GM')

    assert mode(app) == Mode.MENU
    assert app.message == 'Not in the top 10: score not saved'
    assert (tmp_path / 'scores.json').read_text(encoding='utf-8') == saved


@pytest.mark.parametrize('width, height', [
    (5, 5), (99, 5), (5, 99), (99, 99),
])
def test_extreme_maze_shapes_are_playable(
    window: Window, tmp_path: Path, width: int, height: int,
) -> None:
    config = make_config(levels=(LevelSpec(width, height, 42),))
    app = started(window, config, scores_in(tmp_path))
    run_for(app, 1.0)

    assert mode(app) == Mode.PLAYING
    assert app.state is not None
    assert len(app.state.grid) == 2 * height + 1
    assert len(app.state.grid[0]) == 2 * width + 1
