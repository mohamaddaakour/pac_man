"""Tests for key mapping and name entry (frontend.input_handler)."""

from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from frontend.input_handler import (
    Action, NameEntry, NameResult, direction_of, translate,
)
from frontend.window import (
    KEY_BACKSPACE, KEY_DOWN, KEY_ENTER, KEY_ESCAPE, KEY_I, KEY_K, KEY_KP_ENTER,
    KEY_LEFT, KEY_P, KEY_RIGHT, KEY_UP, SCAN_A, SCAN_D, SCAN_S, SCAN_W,
    KeyEvent,
)
from pacman.entities import Direction
from pacman.highscore import Highscores


def key(code: int = 0, scan: int = 0, char: str = '') -> KeyEvent:
    """Build a key press the way the window reports it."""

    return KeyEvent(code, scan, char)


def typed(text: str) -> NameEntry:
    """Return a name entry after typing every character of `text`."""

    entry = NameEntry()
    for char in text:
        entry.handle(key(char=char))

    return entry


@pytest.mark.parametrize('code, action', [
    (KEY_UP, Action.UP), (KEY_DOWN, Action.DOWN),
    (KEY_LEFT, Action.LEFT), (KEY_RIGHT, Action.RIGHT),
])
def test_arrows_move(code: int, action: Action) -> None:
    assert translate(key(code)) == action


@pytest.mark.parametrize('code, scan, action', [
    (pygame.K_w, SCAN_W, Action.UP),      # QWERTY
    (pygame.K_a, SCAN_A, Action.LEFT),
    (pygame.K_s, SCAN_S, Action.DOWN),
    (pygame.K_d, SCAN_D, Action.RIGHT),
    (pygame.K_z, SCAN_W, Action.UP),      # AZERTY: Z sits where W is
    (pygame.K_q, SCAN_A, Action.LEFT),    # AZERTY: Q sits where A is
])
def test_wasd_follows_the_physical_keys(
    code: int, scan: int, action: Action,
) -> None:
    assert translate(key(code, scan)) == action


@pytest.mark.parametrize('code, action', [
    (KEY_ENTER, Action.CONFIRM), (KEY_KP_ENTER, Action.CONFIRM),
    (KEY_ESCAPE, Action.BACK), (KEY_P, Action.PAUSE),
    (KEY_I, Action.TOGGLE_INVISIBLE), (KEY_K, Action.SKIP_LEVEL),
])
def test_command_keys(code: int, action: Action) -> None:
    assert translate(key(code)) == action


@pytest.mark.parametrize('code, scan', [
    (pygame.K_x, pygame.KSCAN_X),
    (pygame.K_a, pygame.KSCAN_Q),     # AZERTY: A sits where Q is
])
def test_other_keys_do_nothing(code: int, scan: int) -> None:
    assert translate(key(code, scan)) is None


@pytest.mark.parametrize('action, direction', [
    (Action.UP, Direction.UP), (Action.DOWN, Direction.DOWN),
    (Action.LEFT, Direction.LEFT), (Action.RIGHT, Direction.RIGHT),
])
def test_movement_actions_give_directions(
    action: Action, direction: Direction,
) -> None:
    assert direction_of(action) == direction


@pytest.mark.parametrize('action', [
    Action.CONFIRM, Action.BACK, Action.PAUSE,
    Action.TOGGLE_INVISIBLE, Action.SKIP_LEVEL,
])
def test_other_actions_have_no_direction(action: Action) -> None:
    assert direction_of(action) is None


def test_name_accepts_letters_digits_and_spaces() -> None:
    assert typed('Ab 42').text == 'Ab 42'


@pytest.mark.parametrize('char', ['é', '!', '-', '\t'])
def test_name_refuses_other_characters(char: str) -> None:
    entry = typed('AB')

    assert entry.handle(key(char=char)) == NameResult.IGNORED
    assert entry.text == 'AB'


def test_name_refuses_an_eleventh_character() -> None:
    entry = typed('ABCDEFGHIJ')

    assert entry.handle(key(char='K')) == NameResult.IGNORED
    assert entry.text == 'ABCDEFGHIJ'


def test_backspace_deletes_and_is_harmless_when_empty() -> None:
    entry = typed('AB')
    backspace = key(KEY_BACKSPACE, char='\x08')

    assert entry.handle(backspace) == NameResult.EDITED
    assert entry.text == 'A'
    entry.handle(backspace)
    assert entry.handle(backspace) == NameResult.IGNORED
    assert entry.text == ''


@pytest.mark.parametrize('code', [KEY_ENTER, KEY_KP_ENTER])
def test_enter_submits_the_stripped_name(code: int) -> None:
    entry = typed(' AB ')

    assert entry.handle(key(code, char='\r')) == NameResult.SUBMIT
    assert entry.text == 'AB'


def test_escape_cancels_without_changing_the_name() -> None:
    entry = typed('AB')

    assert entry.handle(key(KEY_ESCAPE, char='\x1b')) == NameResult.CANCEL
    assert entry.text == 'AB'


def test_game_hotkeys_are_plain_letters_while_typing() -> None:
    entry = NameEntry()
    for code, char in ((KEY_P, 'p'), (KEY_I, 'i'), (KEY_K, 'k')):
        assert entry.handle(key(code, char=char)) == NameResult.EDITED

    assert entry.text == 'pik'


def test_keys_without_a_character_are_ignored() -> None:
    entry = typed('AB')

    assert entry.handle(key(KEY_UP)) == NameResult.IGNORED
    assert entry.text == 'AB'


def test_submitted_names_follow_the_highscore_rules(tmp_path: Path) -> None:
    table = Highscores(str(tmp_path / 'scores.json'))
    table.load()

    good = typed('Player 1')
    good.handle(key(KEY_ENTER, char='\r'))
    assert table.add(good.text, 100)

    blank = typed('   ')
    blank.handle(key(KEY_ENTER, char='\r'))
    assert not table.add(blank.text, 100)
    assert table.last_error is not None
