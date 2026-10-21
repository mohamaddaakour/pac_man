"""Screens: menu, instructions, highscores, pause, end, level change."""

from frontend.window import Window
from frontend.protocols import HighscoresProtocol
from frontend.input_handler import NameEntry
from frontend.constants import (
    BACKGROUND_COLOR,
    HUD_TEXT_COLOR,
    MENU_ITEMS,
    PAUSE_ITEMS
)


def _draw_centered(window: Window, y: int, text: str) -> None:
    width, _ = window.text_size(text)
    x: int = (window.width - width) // 2
    window.put_text(x, y, text, HUD_TEXT_COLOR)


def _draw_title(window: Window, title: str) -> int:
    window.clear(BACKGROUND_COLOR)
    _, height = window.text_size(title)
    y: int = window.height // 4
    _draw_centered(window, y, title)
    return y + height + 40


def draw_menu(window: Window,
              selected: int,
              message: str | None = None) -> None:
    y: int = _draw_title(window, "PAC-MAN")
    _, height = window.text_size("START GAME")

    for i, item in enumerate(MENU_ITEMS):
        marker = "> " if i == selected else "  "
        _draw_centered(window, y, marker + item)
        y += height + 15
    if message:
        y += 20
        _draw_centered(window, y, message)


def draw_instructions(window: Window) -> None:
    y: int = _draw_title(window, "INSTRUCTIONS")
    lines = (
        "Arrow keys or W/A/S/D: Move",
        "P or Esc: Pause / Resume",
        "I: Toggle invisibility",
        "K: Skip level",
        "Enter or Esc: Return to menu",
    )
    for line in lines:
        _draw_centered(window, y, line)
        _, height = window.text_size(line)
        y += height + 12


def draw_highscores(window: Window, highscores: HighscoresProtocol) -> None:
    y: int = _draw_title(window, "HIGHSCORES")
    entries: list[tuple[str, int]] = highscores.top10()
    if not entries:
        _draw_centered(window, y, "No high scores yet.")
        y += 35
    else:
        for index, (name, score) in enumerate(entries, start=1):
            _draw_centered(window, y, f"{index}. {name} - {score}")
            _, height = window.text_size(name)
            y += height + 10
    _draw_centered(window, window.height - 60, "Enter or Esc: Back")


def draw_transition(window: Window, level: int) -> None:
    window.clear(BACKGROUND_COLOR)
    _draw_centered(window, window.height // 2, f"LEVEL {level}")


def draw_pause(window: Window, selected: int) -> None:
    title = "PAUSED"
    _, height = window.text_size(title)
    y: int = window.height // 4
    _draw_centered(window, y, title)
    y += height + 40
    _, height = window.text_size("RESUME")
    for i, item in enumerate(PAUSE_ITEMS):
        marker = "> " if i == selected else "  "
        _draw_centered(window, y, marker + item)
        y += height + 15


def draw_game_end(window: Window,
                  score: int,
                  won: bool,
                  name_entry: NameEntry,
                  can_save: bool,
                  message: str) -> None:
    title = "CONGRATULATIONS!" if won else "GAME OVER"
    y: int = _draw_title(window, title)
    _draw_centered(window, y, f"Final score: {score}")
    _, height = window.text_size("Final score")
    y += height + 25
    if can_save:
        _draw_centered(window, y, "Enter your name:")
        y += height + 15
        _draw_centered(window, y, name_entry.text + "_")
        y += height + 20
        _draw_centered(window, y, "Enter: Save    Esc: Cancel")
    else:
        _draw_centered(window, y, "Your score did not qualify for the top 10.")
        y += height + 20
        _draw_centered(window, y, "Enter or Esc: Return to menu")
    if message:
        _draw_centered(window, window.height - 60, message)
