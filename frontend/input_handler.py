"""Turn key events into game actions and edit the player's name."""

from dataclasses import dataclass
from enum import Enum
from frontend.window import (KeyEvent,
                             KEY_ENTER,
                             KEY_KP_ENTER,
                             KEY_ESCAPE,
                             KEY_BACKSPACE,
                             KEY_UP,
                             KEY_DOWN,
                             KEY_LEFT,
                             KEY_RIGHT,
                             KEY_P,
                             KEY_I,
                             KEY_K,
                             SCAN_W,
                             SCAN_A,
                             SCAN_S,
                             SCAN_D)
from pacman.entities import Direction
from pacman.highscore import NAME_PATTERN


class Action(Enum):
    """What a key asks for; each screen decides what it means."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    CONFIRM = "confirm"
    BACK = "back"
    PAUSE = "pause"
    TOGGLE_INVISIBLE = "invisible"
    SKIP_LEVEL = "skip"


class NameResult(Enum):
    """What a key did to the name being typed."""

    EDITED = "edited"
    SUBMIT = "submit"
    CANCEL = "cancel"
    IGNORED = "ignored"


KEY_TO_ACTION: dict[int, Action] = {KEY_UP: Action.UP,
                                    KEY_DOWN: Action.DOWN,
                                    KEY_LEFT: Action.LEFT,
                                    KEY_RIGHT: Action.RIGHT,
                                    KEY_ENTER: Action.CONFIRM,
                                    KEY_KP_ENTER: Action.CONFIRM,
                                    KEY_ESCAPE: Action.BACK,
                                    KEY_P: Action.PAUSE,
                                    KEY_I: Action.TOGGLE_INVISIBLE,
                                    KEY_K: Action.SKIP_LEVEL}

SCAN_TO_ACTION: dict[int, Action] = {SCAN_W: Action.UP,
                                     SCAN_A: Action.LEFT,
                                     SCAN_S: Action.DOWN,
                                     SCAN_D: Action.RIGHT}

ACTION_TO_DIRECTION: dict[Action, Direction] = {Action.UP: Direction.UP,
                                                Action.DOWN: Direction.DOWN,
                                                Action.LEFT: Direction.LEFT,
                                                Action.RIGHT: Direction.RIGHT}


def translate(event: KeyEvent) -> Action | None:
    """Return the action of a key, or None for other keys.

    Arrows and commands are read by key code. WASD is read by scan
    code (the physical key), so AZERTY players get ZQSD.
    """
    if event.key_code in KEY_TO_ACTION:
        return KEY_TO_ACTION[event.key_code]
    elif event.scan_code in SCAN_TO_ACTION:
        return SCAN_TO_ACTION[event.scan_code]
    else:
        return None


def direction_of(action: Action) -> Direction | None:
    """Return the move direction of an action, or None."""
    return ACTION_TO_DIRECTION.get(action)


@dataclass
class NameEntry:
    """The player name being typed at the end of a game."""

    text: str = ""

    def handle(self, event: KeyEvent) -> NameResult:
        """Apply one key press to the name.

        A typed character is kept only if the name still matches the
        highscore rule (NAME_PATTERN): ASCII letters, digits or spaces,
        at most 10. Enter submits the name without outer spaces.
        """
        if event.key_code == KEY_BACKSPACE:
            if not self.text:
                return NameResult.IGNORED
            self.text = self.text[:-1]
            return NameResult.EDITED
        elif event.key_code in (KEY_ENTER, KEY_KP_ENTER):
            self.text = self.text.strip()
            return NameResult.SUBMIT
        elif event.key_code == KEY_ESCAPE:
            return NameResult.CANCEL
        if not event.typed_character:
            return NameResult.IGNORED
        if NAME_PATTERN.fullmatch(self.text + event.typed_character):
            self.text += event.typed_character
            return NameResult.EDITED
        return NameResult.IGNORED
