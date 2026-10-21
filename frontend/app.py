"""Application state machine: menus, play, pause, name entry, frame tick."""

from enum import Enum
from typing import Callable
from frontend.window import Window, KeyEvent
from frontend.renderer import Renderer
from frontend.protocols import GameStateProtocol, HighscoresProtocol
from frontend.input_handler import (
    Action,
    NameResult,
    translate,
    direction_of,
    NameEntry
)
from frontend.screens import (
    draw_menu,
    draw_instructions,
    draw_highscores,
    draw_transition,
    draw_pause,
    draw_game_end
)
from frontend.constants import (
    TRANSITION_TIME,
    MESSAGE_TIME,
    KEY_REPEAT_DELAY,
    KEY_REPEAT_INTERVAL,
    MENU_ITEMS,
    PAUSE_ITEMS
)
from pacman.config import Config
from pacman.entities import Direction
from pacman.game_state import GameState
from pacman.maze_adapter import MazeError


class Mode(Enum):
    """Which screen the app is showing."""

    MENU = "menu"
    INSTRUCTIONS = "instructions"
    HIGHSCORES = "highscores"
    LEVEL_TRANSITION = "level transition"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_END = "game end"


class App:
    """Connect the window, the game core, the renderer and the screens.

    Keys and frames come from the window; the current mode decides
    what they do.
    """

    def __init__(self,
                 window: Window,
                 config: Config,
                 highscores: HighscoresProtocol,
                 new_game: Callable[[Config],
                                    GameStateProtocol] = GameState) -> None:
        """Start on the menu, with no game yet.

        Args:
            window: The open game window.
            config: Validated settings used to build each new game.
            highscores: The loaded table, shared by every game.
            new_game: Builds a game from the config; tests pass a fake.
        """
        self.window: Window = window
        self.config: Config = config
        self.highscores: HighscoresProtocol = highscores
        self.new_game: Callable[[Config], GameStateProtocol] = new_game
        self.renderer: Renderer = Renderer(self.window)
        self.mode: Mode = Mode.MENU
        self.state: GameStateProtocol | None = None
        self.menu_selected: int = 0
        self.pause_selected: int = 0
        self.transition_timer: float = 0.0
        self.message_timer: float = 0.0
        self.name_entry: NameEntry = NameEntry()
        self.won: bool = False
        self.final_score: int = 0
        self.can_save: bool = False
        self.message: str | None = None

    def run(self) -> None:
        """Connect the window callbacks and run until it closes."""
        self.window.on_key(self.on_key)
        self.window.on_frame(self.on_frame)
        self.window.run()

    def on_key(self, event: KeyEvent) -> None:
        """Handle one key press according to the current mode.

        On the end screen keys go to the name entry instead of being
        translated, so game hotkeys like P, I and K only type letters.
        """
        action: Action | None = translate(event)
        if self.mode == Mode.MENU:
            if action == Action.UP:
                self.menu_selected = (self.menu_selected - 1) % len(MENU_ITEMS)
                return
            elif action == Action.DOWN:
                self.menu_selected = (self.menu_selected + 1) % len(MENU_ITEMS)
                return
            elif action == Action.BACK:
                self.window.close()
                return
            elif action != Action.CONFIRM:
                return
            selected_item: str = MENU_ITEMS[self.menu_selected]
            if selected_item == "START GAME":
                self.message = None
                self.message_timer = 0
                try:
                    self.state = self.new_game(self.config)
                    self.mode = Mode.LEVEL_TRANSITION
                    self.transition_timer = TRANSITION_TIME
                except MazeError as e:
                    self.message = str(e)
                    self.message_timer = MESSAGE_TIME
            elif selected_item == "VIEW HIGHSCORES":
                self.mode = Mode.HIGHSCORES
            elif selected_item == "INSTRUCTIONS":
                self.mode = Mode.INSTRUCTIONS
            elif selected_item == "EXIT":
                self.window.close()
        elif self.mode in (Mode.INSTRUCTIONS, Mode.HIGHSCORES):
            if action == Action.CONFIRM or action == Action.BACK:
                self.mode = Mode.MENU
        elif self.mode == Mode.LEVEL_TRANSITION:
            return
        elif self.mode == Mode.PLAYING:
            if self.state is None:
                self.mode = Mode.MENU
                return
            if action in (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT):
                direction: Direction | None = direction_of(action)
                if direction is not None:
                    self.state.set_direction(direction)
            elif action in (Action.PAUSE, Action.BACK):
                self.pause_selected = 0
                self.mode = Mode.PAUSED
                return
            elif action == Action.TOGGLE_INVISIBLE:
                self.state.toggle_invisibility()
            elif action == Action.SKIP_LEVEL:
                self.state.skip_level()
        elif self.mode == Mode.PAUSED:
            if action == Action.UP:
                self.pause_selected = (
                    self.pause_selected - 1) % len(PAUSE_ITEMS)
                return
            elif action == Action.DOWN:
                self.pause_selected = (
                    self.pause_selected + 1) % len(PAUSE_ITEMS)
                return
            elif action in (Action.PAUSE, Action.BACK):
                self.mode = Mode.PLAYING
                return
            elif action != Action.CONFIRM:
                return
            selected_pause_item: str = PAUSE_ITEMS[self.pause_selected]
            if selected_pause_item == "RESUME":
                self.mode = Mode.PLAYING
            elif selected_pause_item == "MAIN MENU":
                self._return_to_menu()
        elif self.mode == Mode.GAME_END:
            if self.can_save:
                result: NameResult = self.name_entry.handle(event)
                if result == NameResult.SUBMIT:
                    if self.highscores.add(self.name_entry.text,
                                           self.final_score):
                        self._return_to_menu("Highscore saved!")
                    else:
                        self.message = self.highscores.last_error
                elif result == NameResult.CANCEL:
                    self._return_to_menu()
            elif action in (Action.CONFIRM, Action.BACK):
                self._return_to_menu()

    def on_frame(self, dt: float) -> None:
        """Advance one frame: update the game only while playing, then
        draw the current mode.

        Pausing works by not calling update, which freezes the timer.

        Args:
            dt: Seconds since the last frame.
        """
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)
            if self.message_timer == 0:
                self.message = None
        if self.state is None:
            if self.mode == Mode.MENU:
                draw_menu(self.window, self.menu_selected, self.message)
            elif self.mode == Mode.INSTRUCTIONS:
                draw_instructions(self.window)
            elif self.mode == Mode.HIGHSCORES:
                draw_highscores(self.window, self.highscores)
            return
        if self.mode == Mode.PLAYING:
            self.state.update(dt)
            self.renderer.draw(self.state, dt)
            if self.state.status == "playing":
                return
            elif self.state.status == "level_won":
                try:
                    self.state.next_level()
                except MazeError as e:
                    self._return_to_menu(str(e))
                    return
                self.transition_timer = TRANSITION_TIME
                self.mode = Mode.LEVEL_TRANSITION
            elif self.state.status == "game_won":
                self._finish_game(True)
            elif self.state.status == "game_over":
                self._finish_game(False)
        elif self.mode == Mode.PAUSED:
            self.renderer.draw(self.state, 0)
            draw_pause(self.window, self.pause_selected)
        elif self.mode == Mode.LEVEL_TRANSITION:
            self.transition_timer = max(0.0, self.transition_timer - dt)
            draw_transition(self.window, self.state.level)
            if self.transition_timer <= 0:
                self.mode = Mode.PLAYING
        elif self.mode == Mode.GAME_END:
            draw_game_end(self.window,
                          self.final_score,
                          self.won,
                          self.name_entry,
                          self.can_save,
                          self.message or "")

    def _finish_game(self, won: bool) -> None:
        """Show the end screen; ask a name only for a top 10 score."""
        self.won = won
        self.final_score = self.state.score if self.state else 0
        self.can_save = self.highscores.qualifies(self.final_score)
        self.name_entry = NameEntry()
        self.message = None
        self._set_name_entry_repeat(self.can_save)
        self.mode = Mode.GAME_END

    def _return_to_menu(self, message: str | None = None) -> None:
        """Drop the current game and show the menu with a message."""
        self._set_name_entry_repeat(False)
        self.state = None
        self.renderer.reset()
        self.name_entry = NameEntry()
        self.can_save = False
        self.pause_selected = 0
        self.message = message
        self.message_timer = MESSAGE_TIME if message else 0
        self.mode = Mode.MENU

    def _set_name_entry_repeat(self, enabled: bool) -> None:
        """Repeat held keys while typing a name, and nowhere else."""
        if enabled:
            self.window.set_key_repeat(KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL)
        else:
            self.window.set_key_repeat(0, 0)
