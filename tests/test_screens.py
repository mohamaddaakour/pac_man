"""Tests for the menu, pause, transition and end screens (frontend.screens)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace

import pygame
import pytest

from frontend.app import App
from frontend.constants import (
    ERROR_COLOR, HINT_COLOR, HUD_TEXT_COLOR, MENU_SCORES, SELECTED_COLOR,
    TITLE_COLOR, WALL_COLOR, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from frontend.input_handler import NameEntry
from frontend.screens import Screens
from frontend.window import KEY_ENTER, KEY_K, KEY_P, KeyEvent, Window
from pacman.config import Config, LevelSpec
from tests.core_helpers import make_config
from tests.fakes import FakeHighscores, FakeState, make_state

Text = tuple[str, int, int, tuple[int, ...]]


@pytest.fixture
def window() -> Iterator[Window]:
    """Open a headless window of the real game size."""

    win = Window(WINDOW_WIDTH, WINDOW_HEIGHT, 'test', headless_ok=True)
    yield win
    pygame.quit()


@pytest.fixture
def texts(
    window: Window, monkeypatch: pytest.MonkeyPatch,
) -> Iterator[list[Text]]:
    """Record every text drawn as (text, x, y, colour)."""

    drawn: list[Text] = []
    real = window.put_text

    def recording(x: int, y: int, text: str, color: tuple[int, ...]) -> None:
        """Remember the text, then draw it."""
        drawn.append((text, x, y, tuple(color)))
        real(x, y, text, color)

    monkeypatch.setattr(window, 'put_text', recording)
    yield drawn


def strings(drawn: list[Text]) -> list[str]:
    """Return only the drawn strings, in drawing order."""

    return [text for text, _, _, _ in drawn]


def colour_of(drawn: list[Text], wanted: str) -> tuple[int, ...]:
    """Return the colour a string was drawn in."""

    return next(color for text, _, _, color in drawn if text == wanted)


def scores(count: int) -> FakeHighscores:
    """Return a table with `count` entries, best first."""

    return FakeHighscores(
        entries=[(f'PLAYER{i}', 1000 - i * 10) for i in range(count)],
    )


def test_screens_never_build_images_while_drawing(
    window: Window, monkeypatch: pytest.MonkeyPatch,
) -> None:
    screens = Screens(window, make_config())
    calls: list[int] = []

    def counting(width: int, height: int, opaque: bool) -> object:
        """Count calls instead of building images."""
        calls.append(width)
        raise AssertionError('new_image called while drawing')

    monkeypatch.setattr(window, 'new_image', counting)
    screens.draw_menu(0, scores(10), 'message')
    screens.draw_instructions()
    screens.draw_highscores(scores(10))
    screens.draw_transition(1, 10)
    screens.draw_pause(0)
    screens.draw_game_end(500, True, NameEntry('GM'), 'error')
    screens.draw_game_end(500, False, NameEntry(), '')

    assert calls == []


def test_menu_highlights_the_selected_item(
    window: Window, texts: list[Text],
) -> None:
    Screens(window, make_config()).draw_menu(1, scores(0))

    assert colour_of(texts, '> VIEW HIGHSCORES') == SELECTED_COLOR
    assert colour_of(texts, '  START GAME') == HUD_TEXT_COLOR


def test_menu_shows_the_best_scores(
    window: Window, texts: list[Text],
) -> None:
    Screens(window, make_config()).draw_menu(0, scores(10), 'Saved!')
    shown = strings(texts)

    assert colour_of(texts, 'TOP SCORES') == TITLE_COLOR
    assert '1. PLAYER0 - 1000' in shown
    assert f'{MENU_SCORES}. PLAYER{MENU_SCORES - 1} - ' \
           f'{1000 - (MENU_SCORES - 1) * 10}' in shown
    assert not any(text.startswith(f'{MENU_SCORES + 1}.') for text in shown)
    assert 'Saved!' in shown


def test_menu_says_when_there_are_no_scores(
    window: Window, texts: list[Text],
) -> None:
    Screens(window, make_config()).draw_menu(0, scores(0))

    assert 'No scores yet' in strings(texts)


def test_highscores_table_lists_ten_aligned_rows(
    window: Window, texts: list[Text],
) -> None:
    Screens(window, make_config()).draw_highscores(scores(10))
    rows = [(x, y) for text, x, y, _ in texts if text.startswith('PLAYER')]
    numbers = [text for text, _, _, _ in texts if text.endswith('.')]

    assert len(rows) == 10
    assert len({x for x, _ in rows}) == 1           # one name column
    assert numbers == [f'{rank}.' for rank in range(1, 11)]
    assert colour_of(texts, 'Enter or Esc: Back') == HINT_COLOR


def test_instructions_read_the_rules_from_the_config(
    window: Window, texts: list[Text],
) -> None:
    config = replace(make_config(), points_per_pacgum=7, lives=5)
    Screens(window, config).draw_instructions()
    shown = strings(texts)

    assert 'Pacgum: 7 points' in shown
    assert 'Lives: 5' in shown
    assert 'Clear all 10 levels to win' in shown
    assert colour_of(texts, 'CONTROLS') == TITLE_COLOR
    assert colour_of(texts, 'RULES') == TITLE_COLOR


def test_instructions_count_every_configured_level(
    window: Window, texts: list[Text],
) -> None:
    levels = tuple(LevelSpec(15, 15, None) for _ in range(12))
    Screens(window, make_config(levels=levels)).draw_instructions()

    assert 'Clear all 12 levels to win' in strings(texts)


def test_pause_highlights_resume(window: Window, texts: list[Text]) -> None:
    Screens(window, make_config()).draw_pause(0)

    assert 'PAUSED' in strings(texts)
    assert colour_of(texts, '> RESUME') == SELECTED_COLOR
    assert colour_of(texts, '  MAIN MENU') == HUD_TEXT_COLOR


def test_end_screen_asks_for_a_name_and_shows_errors(
    window: Window, texts: list[Text],
) -> None:
    Screens(window, make_config()).draw_game_end(
        500, False, NameEntry('GM'), 'Bad name',
    )
    shown = strings(texts)

    assert 'Final score: 500' in shown
    assert 'GM_' in shown
    assert colour_of(texts, 'Bad name') == ERROR_COLOR


def test_victory_screen_also_asks_for_a_name(
    window: Window, texts: list[Text],
) -> None:
    Screens(window, make_config()).draw_game_end(5, True, NameEntry(), '')
    shown = strings(texts)

    assert 'Final score: 5' in shown
    assert 'Enter your name:' in shown
    assert '_' in shown
    assert colour_of(texts, 'Enter: Save    Esc: Cancel') == HINT_COLOR


def started(window: Window, state: FakeState) -> App:
    """Return an app on the first frame of level 1."""

    def new_game(config: Config) -> FakeState:
        """Return the prepared fake game."""
        return state

    app = App(window, make_config(), FakeHighscores(), new_game=new_game)
    app.on_frame(1 / 60)                       # the menu is on screen
    app.on_key(KeyEvent(KEY_ENTER, 0, '\r'))
    app.on_frame(1 / 60)
    return app


def screen_pixels() -> bytes:
    """Return a copy of every pixel on the screen."""

    surface = pygame.display.get_surface()
    assert surface is not None
    return pygame.image.tobytes(surface, 'RGB')


def test_transition_shows_the_maze_from_its_first_frame(
    window: Window, texts: list[Text],
) -> None:
    started(window, make_state(15, 15))
    surface = pygame.display.get_surface()
    assert surface is not None

    assert 'LEVEL 1/10' in strings(texts)
    assert any(
        tuple(surface.get_at((x, y)))[:3] == WALL_COLOR
        for x in range(0, WINDOW_WIDTH, 4) for y in range(0, WINDOW_HEIGHT, 4)
    )


def test_transition_panel_does_not_darken_over_time(window: Window) -> None:
    app = started(window, make_state(15, 15))
    first = screen_pixels()
    for _ in range(30):
        app.on_frame(1 / 60)

    assert screen_pixels() == first


def test_level_change_shows_the_new_level_everywhere(
    window: Window, texts: list[Text],
) -> None:
    app = started(window, make_state(15, 15))
    for _ in range(130):
        app.on_frame(1 / 60)
    texts.clear()

    app.on_key(KeyEvent(KEY_K, 0, 'k'))
    app.on_frame(1 / 60)                       # level 2 starts
    app.on_frame(1 / 60)                       # first transition frame
    shown = strings(texts)

    # The first frame of the transition draws level 2 twice: in the HUD
    # (the game is redrawn under the panel) and on the panel itself.
    assert shown.count('LEVEL 2/10') == 2


def test_pause_draws_over_the_frozen_game(
    window: Window, texts: list[Text],
) -> None:
    app = started(window, make_state(15, 15))
    for _ in range(130):
        app.on_frame(1 / 60)
    app.on_key(KeyEvent(KEY_P, 0, 'p'))
    texts.clear()
    app.on_frame(1 / 60)
    shown = strings(texts)

    assert 'LEVEL 1/10' in shown               # the HUD is still visible
    assert shown.index('LEVEL 1/10') < shown.index('PAUSED')
