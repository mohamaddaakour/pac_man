"""Tests for the application state machine (frontend.app)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pygame
import pytest

from frontend.app import App, Mode
from frontend.constants import (
    KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL, MESSAGE_TIME, TRANSITION_TIME,
    WINDOW_HEIGHT, WINDOW_WIDTH,
)
from frontend.window import (
    KEY_DOWN, KEY_ENTER, KEY_ESCAPE, KEY_I, KEY_K, KEY_P, KEY_UP, SCAN_A,
    KeyEvent, Window,
)
from pacman.config import Config
from pacman.entities import Direction
from pacman.highscore import Highscores
from pacman.maze_adapter import MazeError
from tests.core_helpers import make_config
from tests.fakes import FakeHighscores, FakeState, make_state

UP, DOWN = KeyEvent(KEY_UP, 0, ''), KeyEvent(KEY_DOWN, 0, '')
ENTER = KeyEvent(KEY_ENTER, 0, '\r')
ESCAPE = KeyEvent(KEY_ESCAPE, 0, '\x1b')
PAUSE = KeyEvent(KEY_P, 0, 'p')
INVISIBLE = KeyEvent(KEY_I, 0, 'i')
SKIP = KeyEvent(KEY_K, 0, 'k')
LEFT_WASD = KeyEvent(0, SCAN_A, 'a')


@pytest.fixture
def window() -> Iterator[Window]:
    """Open a headless window of the real game size."""

    win = Window(WINDOW_WIDTH, WINDOW_HEIGHT, 'test', headless_ok=True)
    yield win
    pygame.quit()


def make_app(
    window: Window, state: FakeState | None = None,
    scores: FakeHighscores | None = None,
) -> tuple[App, FakeState, FakeHighscores]:
    """Build an app whose new games are the given fake state."""

    game = state if state is not None else make_state()
    table = scores if scores is not None else FakeHighscores()

    def new_game(config: Config) -> FakeState:
        """Return the prepared fake game."""
        return game

    return App(window, make_config(), table, new_game=new_game), game, table


def run_for(app: App, seconds: float) -> None:
    """Run frames at 60 per second for about `seconds`."""

    for _ in range(int(seconds * 60) + 1):
        app.on_frame(1 / 60)


def type_text(app: App, text: str) -> None:
    """Type characters the way the window reports them."""

    for char in text:
        app.on_key(KeyEvent(0, 0, char))


def mode(app: App) -> Mode:
    """Read the current mode (a call, so mypy does not freeze its value)."""

    return app.mode


def playing(
    window: Window, state: FakeState | None = None,
    scores: FakeHighscores | None = None,
) -> tuple[App, FakeState, FakeHighscores]:
    """Return an app already past the first level transition."""

    app, game, table = make_app(window, state, scores)
    app.on_key(ENTER)
    run_for(app, TRANSITION_TIME + 0.1)
    assert mode(app) == Mode.PLAYING
    return app, game, table


def test_app_starts_on_the_menu(window: Window) -> None:
    app, _, _ = make_app(window)
    app.on_frame(1 / 60)

    assert mode(app) == Mode.MENU
    assert app.state is None


def test_menu_selection_wraps_around(window: Window) -> None:
    app, _, _ = make_app(window)

    app.on_key(UP)
    assert app.menu_selected == 3
    app.on_key(DOWN)
    assert app.menu_selected == 0


@pytest.mark.parametrize('index, screen', [
    (1, Mode.HIGHSCORES), (2, Mode.INSTRUCTIONS),
])
def test_menu_screens_open_and_close(
    window: Window, index: int, screen: Mode,
) -> None:
    app, _, _ = make_app(window)
    for _ in range(index):
        app.on_key(DOWN)

    app.on_key(ENTER)
    app.on_frame(1 / 60)
    assert mode(app) == screen
    app.on_key(ESCAPE)
    assert mode(app) == Mode.MENU


@pytest.mark.parametrize('keys', [[UP, ENTER], [ESCAPE]])
def test_exit_and_escape_close_the_window(
    window: Window, keys: list[KeyEvent],
) -> None:
    app, _, _ = make_app(window)
    for key in keys:
        app.on_key(key)

    assert window.closed


def test_start_shows_the_level_then_plays(window: Window) -> None:
    app, game, _ = make_app(window)
    app.on_key(ENTER)

    assert mode(app) == Mode.LEVEL_TRANSITION
    run_for(app, TRANSITION_TIME - 0.2)
    assert mode(app) == Mode.LEVEL_TRANSITION
    assert game.updates == []                  # the timer is frozen
    run_for(app, 0.3)
    assert mode(app) == Mode.PLAYING


def test_keys_are_ignored_during_the_transition(window: Window) -> None:
    app, game, _ = make_app(window)
    app.on_key(ENTER)
    for key in (PAUSE, SKIP, INVISIBLE, ESCAPE):
        app.on_key(key)

    assert mode(app) == Mode.LEVEL_TRANSITION
    assert game.status == 'playing' and not game.invisible


def test_playing_updates_the_game_and_steers(window: Window) -> None:
    app, game, _ = playing(window)
    game.updates.clear()

    run_for(app, 0.1)
    app.on_key(UP)
    app.on_key(LEFT_WASD)

    assert game.updates and all(dt > 0 for dt in game.updates)
    assert game.directions == [Direction.UP, Direction.LEFT]


def test_cheat_keys_reach_the_game(window: Window) -> None:
    app, game, _ = playing(window)

    app.on_key(INVISIBLE)
    assert game.invisible
    app.on_key(SKIP)
    app.on_frame(1 / 60)

    assert game.next_level_calls == 1
    assert game.level == 2
    assert mode(app) == Mode.LEVEL_TRANSITION


@pytest.mark.parametrize('key', [PAUSE, ESCAPE])
def test_pause_freezes_the_game(window: Window, key: KeyEvent) -> None:
    app, game, _ = playing(window)

    app.on_key(key)
    game.updates.clear()
    run_for(app, 1.0)

    assert mode(app) == Mode.PAUSED
    assert game.updates == []
    app.on_key(key)
    assert mode(app) == Mode.PLAYING


def test_resuming_never_quits_the_game(window: Window) -> None:
    app, game, _ = playing(window)

    app.on_key(PAUSE)
    app.on_key(DOWN)               # MAIN MENU highlighted
    app.on_key(PAUSE)              # resume anyway

    assert mode(app) == Mode.PLAYING
    assert app.state is game


def test_pause_always_opens_on_resume(window: Window) -> None:
    app, _, _ = playing(window)

    app.on_key(PAUSE)
    app.on_key(DOWN)
    app.on_key(PAUSE)
    app.on_key(PAUSE)
    app.on_key(ENTER)

    assert mode(app) == Mode.PLAYING


def test_main_menu_from_pause_drops_the_game(window: Window) -> None:
    app, _, _ = playing(window)

    app.on_key(PAUSE)
    app.on_key(DOWN)
    app.on_key(ENTER)

    assert mode(app) == Mode.MENU
    assert app.state is None


def test_winning_the_last_level_ends_the_game(window: Window) -> None:
    state = make_state()
    state.level, state.score = state.total_levels, 1230
    app, _, _ = playing(window, state=state)

    app.on_key(SKIP)
    app.on_frame(1 / 60)

    assert mode(app) == Mode.GAME_END
    assert app.won and app.final_score == 1230


def test_losing_ends_the_game(window: Window) -> None:
    app, game, _ = playing(window)

    game.status = 'game_over'
    app.on_frame(1 / 60)

    assert mode(app) == Mode.GAME_END
    assert not app.won


def ended(
    window: Window, scores: FakeHighscores | None = None,
) -> tuple[App, FakeState, FakeHighscores]:
    """Return an app on the end screen after losing."""

    app, game, table = playing(window, scores=scores)
    game.score = 500
    game.status = 'game_over'
    app.on_frame(1 / 60)
    return app, game, table


def test_name_is_saved_then_back_to_the_menu(window: Window) -> None:
    app, _, table = ended(window)

    type_text(app, 'GM')
    app.on_key(ENTER)

    assert table.entries == [('GM', 500)]
    assert mode(app) == Mode.MENU
    assert app.message == 'Highscore saved!'
    run_for(app, MESSAGE_TIME + 0.1)
    assert app.message is None


def test_failed_save_stays_for_a_retry(window: Window) -> None:
    app, _, table = ended(window, scores=FakeHighscores(accept=False))

    type_text(app, 'GM')
    app.on_key(ENTER)
    assert mode(app) == Mode.GAME_END
    assert app.message == table.last_error

    table.accept = True
    app.on_key(ENTER)
    assert mode(app) == Mode.MENU
    assert table.entries == [('GM', 500)]


def test_game_hotkeys_type_letters_on_the_end_screen(window: Window) -> None:
    app, game, _ = ended(window)

    for key in (PAUSE, INVISIBLE, SKIP):
        app.on_key(key)

    assert mode(app) == Mode.GAME_END
    assert app.name_entry.text == 'pik'
    assert not game.invisible


def test_escape_on_the_end_screen_saves_nothing(window: Window) -> None:
    app, _, table = ended(window)

    type_text(app, 'GM')
    app.on_key(ESCAPE)

    assert mode(app) == Mode.MENU
    assert table.entries == []


def test_score_outside_the_top_ten_still_asks_a_name(window: Window) -> None:
    app, _, table = ended(window, scores=FakeHighscores(qualify=False))

    assert not app.can_save
    type_text(app, 'GM')
    assert app.name_entry.text == 'GM'
    app.on_key(ENTER)

    assert mode(app) == Mode.MENU
    assert app.message == 'Not in the top 10: score not saved'
    assert table.entries == []


def test_blank_name_is_refused_by_the_real_table(
    window: Window, tmp_path: Path,
) -> None:
    table = Highscores(str(tmp_path / 'scores.json'))
    table.load()
    app, game, _ = make_app(window)
    app.highscores = table
    app.on_key(ENTER)
    run_for(app, TRANSITION_TIME + 0.1)
    game.status = 'game_over'
    app.on_frame(1 / 60)

    type_text(app, '   ')
    app.on_key(ENTER)

    assert mode(app) == Mode.GAME_END
    assert app.message is not None
    assert table.top10() == []


def test_maze_error_at_start_stays_on_the_menu(window: Window) -> None:
    def broken(config: Config) -> FakeState:
        """Fail like a maze generator that cannot build a level."""
        raise MazeError('generator failed')

    app = App(window, make_config(), FakeHighscores(), new_game=broken)
    app.on_key(ENTER)

    assert mode(app) == Mode.MENU
    assert app.message == 'generator failed'


def test_maze_error_at_level_change_returns_to_the_menu(
    window: Window,
) -> None:
    class Broken(FakeState):
        """A game whose next maze cannot be built."""

        def next_level(self) -> None:
            """Fail like the core does."""
            raise MazeError('could not build level 2')

    plain = make_state()
    state = Broken(plain.grid, plain.player, plain.ghosts,
                   plain.pacgums, plain.super_pacgums)
    app, _, _ = playing(window, state=state)

    app.on_key(SKIP)
    app.on_frame(1 / 60)

    assert mode(app) == Mode.MENU
    assert app.message == 'could not build level 2'
    assert app.state is None


@pytest.mark.parametrize('qualify', [True, False])
def test_key_repeat_only_while_typing_a_name(
    window: Window, qualify: bool,
) -> None:
    app, game, _ = playing(window, scores=FakeHighscores(qualify=qualify))
    assert pygame.key.get_repeat() == (0, 0)

    game.status = 'game_over'
    app.on_frame(1 / 60)
    assert pygame.key.get_repeat() == (KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL)

    app.on_key(ESCAPE)
    assert pygame.key.get_repeat() == (0, 0)
