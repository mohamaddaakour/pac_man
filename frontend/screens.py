"""Screens: menu, instructions, highscores, pause, end, level change."""

from frontend.window import Image, Window
from frontend.sprites import scale_up
from frontend.protocols import HighscoresProtocol
from frontend.input_handler import NameEntry
from frontend.constants import (
    BACKGROUND_COLOR,
    HUD_TEXT_COLOR,
    MENU_ITEMS,
    PAUSE_ITEMS,
    TITLE_COLOR,
    SELECTED_COLOR,
    HINT_COLOR,
    ERROR_COLOR,
    PANEL_COLOR,
    PANEL_SIZE,
    TITLE_SCALE,
    MENU_SCORES
)
from pacman.config import Config
from pacman.levels import plan_levels


class Screens:
    """Draw every screen apart from the game itself.

    Titles and the panel are images built once here; drawing a
    screen only places them and writes text.
    """

    def __init__(self, window: Window, config: Config) -> None:
        """Build the titles and the panel, and count the levels to play."""
        self.window: Window = window
        self.config: Config = config
        self.menu_title: Image = self._make_title_image("PAC-MAN", TITLE_COLOR)
        self.instructions_title: Image = self._make_title_image(
            "INSTRUCTIONS", TITLE_COLOR)
        self.highscores_title: Image = self._make_title_image(
            "HIGHSCORES", TITLE_COLOR)
        self.pause_panel: Image = self.window.new_image(*PANEL_SIZE, False)
        self.pause_panel.pixels[:] = bytes(PANEL_COLOR) * (
            PANEL_SIZE[0] * PANEL_SIZE[1]
        )
        self.victory_title: Image = self._make_title_image(
            "CONGRATULATIONS", TITLE_COLOR)
        self.game_over_title: Image = self._make_title_image(
            "GAME OVER", ERROR_COLOR)
        self.total_levels: int = len(plan_levels(self.config.levels))

    def _make_title_image(self, text: str, color: tuple[int, ...]) -> Image:
        """Render `text` once and enlarge it into a big title image.

        The text pixels are scaled in Python (scale_up), because pygame
        scaling has no MLX equivalent.
        """
        pixels, width, height = self.window.text_pixels(text, color)
        scaled_pixels: bytes = scale_up(pixels, width, height, TITLE_SCALE)
        scaled_width: int = width * TITLE_SCALE
        scaled_height: int = height * TITLE_SCALE
        title_image: Image = self.window.new_image(scaled_width,
                                                   scaled_height, False)
        title_image.pixels[:] = scaled_pixels
        return title_image

    def _draw_panel(self) -> None:
        """Draw the dark see-through panel in the middle of the window."""
        x: int = (self.window.width - PANEL_SIZE[0]) // 2
        y: int = (self.window.height - PANEL_SIZE[1]) // 2
        self.window.put_image(self.pause_panel, x, y)

    def _draw_centered(self, y: int, text: str,
                       color: tuple[int, ...] = HUD_TEXT_COLOR) -> None:
        """Write `text` centred horizontally at height `y`."""
        width, _ = self.window.text_size(text)
        x: int = (self.window.width - width) // 2
        self.window.put_text(x, y, text, color)

    def _draw_title(self, image: Image) -> int:
        """Clear the window, draw a title, return the y below it."""
        self.window.clear(BACKGROUND_COLOR)
        y: int = self.window.height // 4
        x: int = (self.window.width - image.width) // 2
        self.window.put_image(image, x, y)
        return y + image.height + 40

    def draw_menu(self,
                  selected: int,
                  highscores: HighscoresProtocol,
                  message: str | None = None) -> None:
        """Draw the main menu, a message and the best scores.

        Args:
            selected: Index of the highlighted item.
            highscores: Table whose best entries are listed.
            message: Optional line, such as a saved score or an error.
        """
        y: int = self._draw_title(self.menu_title)
        _, height = self.window.text_size("START GAME")
        for i, item in enumerate(MENU_ITEMS):
            marker: str = "> " if i == selected else "  "
            color: tuple[int, ...] = (SELECTED_COLOR
                                      if i == selected
                                      else HUD_TEXT_COLOR)
            self._draw_centered(y, marker + item, color)
            y += height + 15
        y += 20
        if message:
            self._draw_centered(y, message)
            y += height + 20
        _, row_height = self.window.text_size("10. Player1234 - 999999")
        self._draw_centered(y, "TOP SCORES", TITLE_COLOR)
        y += row_height + 10
        entries: list[tuple[str, int]] = highscores.top10()[:MENU_SCORES]
        if not entries:
            self._draw_centered(y, "No scores yet")
        else:
            for index, (name, score) in enumerate(entries, start=1):
                self._draw_centered(y, f"{index}. {name} - {score}")
                y += row_height + 10

    def draw_instructions(self) -> None:
        """Draw the controls and the rules, read from the config."""
        y: int = self._draw_title(self.instructions_title)
        self._draw_centered(y, "CONTROLS", TITLE_COLOR)
        _, height = self.window.text_size("CONTROLS")
        y += height + 8
        controls: tuple[str, ...] = (
            "Arrow keys or W/A/S/D: Move",
            "P or Esc: Pause / Resume",
            "I: Toggle invisibility",
            "K: Skip level"
        )
        for line in controls:
            self._draw_centered(y, line)
            _, height = self.window.text_size(line)
            y += height + 5
        y += 8
        self._draw_centered(y, "RULES", TITLE_COLOR)
        _, height = self.window.text_size("RULES")
        y += height + 8
        rules: tuple[str, ...] = (
            f"Pacgum: {self.config.points_per_pacgum} points",
            f"Super-pacgum: {self.config.points_per_super_pacgum} points",
            f"Ghost: {self.config.points_per_ghost} points",
            f"Ghosts are edible for: {self.config.edible_duration:g} seconds",
            f"Ghost respawn: {self.config.ghost_respawn_time:g} seconds",
            f"Lives: {self.config.lives}",
            f"Time limit: {self.config.level_max_time:g} seconds per level",
            "Eat every pacgum to clear each level",
            f"Clear all {self.total_levels} levels to win"
        )
        for line in rules:
            self._draw_centered(y, line)
            _, height = self.window.text_size(line)
            y += height + 5
        self._draw_centered(self.window.height - 45,
                            "Enter or Esc: Return to menu", HINT_COLOR)

    def draw_highscores(self, highscores: HighscoresProtocol) -> None:
        """Draw the top 10 as a ranked table with aligned columns."""
        y: int = self._draw_title(self.highscores_title)
        entries: list[tuple[str, int]] = highscores.top10()
        if not entries:
            self._draw_centered(y, "No high scores yet.")
            y += 35
        else:
            rank_x: int = self.window.width // 6
            name_x: int = self.window.width // 3
            score_x: int = self.window.width * 5 // 6
            self.window.put_text(rank_x, y, "RANK", HUD_TEXT_COLOR)
            self.window.put_text(name_x, y, "NAME", HUD_TEXT_COLOR)
            self.window.put_text(score_x, y, "SCORE", HUD_TEXT_COLOR)
            _, height = self.window.text_size("RANK")
            y += height + 10
            _, row_height = self.window.text_size("Player1234")
            for index, (name, score) in enumerate(entries, start=1):
                self.window.put_text(rank_x, y,
                                     str(index) + ".", HUD_TEXT_COLOR)
                self.window.put_text(name_x, y, name, HUD_TEXT_COLOR)
                self.window.put_text(score_x, y, str(score), HUD_TEXT_COLOR)
                y += row_height + 10
        self._draw_centered(self.window.height - 60,
                            "Enter or Esc: Back", HINT_COLOR)

    def draw_transition(self, level: int, total_levels: int) -> None:
        """Draw "LEVEL N/TOTAL" on the panel, over the new maze."""
        self._draw_panel()
        text: str = f"LEVEL {level}/{total_levels}"
        _, height = self.window.text_size(text)
        y: int = (self.window.height - height) // 2
        self._draw_centered(y, text)

    def draw_pause(self, selected: int) -> None:
        """Draw the pause menu on the panel, over the frozen game."""
        self._draw_panel()
        panel_y: int = (self.window.height - PANEL_SIZE[1]) // 2
        title: str = "PAUSED"
        _, height = self.window.text_size(title)
        y: int = panel_y + 45
        self._draw_centered(y, title)
        y += height + 40
        _, height = self.window.text_size("RESUME")
        for i, item in enumerate(PAUSE_ITEMS):
            marker: str = "> " if i == selected else "  "
            color: tuple[int, ...] = (SELECTED_COLOR
                                      if i == selected
                                      else HUD_TEXT_COLOR)
            self._draw_centered(y, marker + item, color)
            y += height + 15

    def draw_game_end(self,
                      score: int,
                      won: bool,
                      name_entry: NameEntry,
                      can_save: bool,
                      message: str) -> None:
        """Draw the game over or victory screen with the final score.

        Args:
            score: Final score of the game.
            won: True after the last level, False after losing.
            name_entry: The name being typed.
            can_save: Ask for a name, or explain the score is too low.
            message: Error from the last save attempt, or empty.
        """
        y: int = self._draw_title(self.victory_title
                                  if won
                                  else self.game_over_title)
        self._draw_centered(y, f"Final score: {score}")
        _, height = self.window.text_size(f"Final score: {score}")
        y += height + 25
        if can_save:
            self._draw_centered(y, "Enter your name:")
            _, height = self.window.text_size("Enter your name:")
            y += height + 10
            self._draw_centered(y, name_entry.text + "_")
            _, height = self.window.text_size(name_entry.text + "_")
            y += height + 15
            self._draw_centered(y, "Enter: Save    Esc: Cancel", HINT_COLOR)
            _, height = self.window.text_size("Enter: Save    Esc: Cancel")
            y += height + 10
        else:
            self._draw_centered(y, "Your score didn't qualify for the top 10.")
            _, height = self.window.text_size(
                "Your score didn't qualify for the top 10.")
            y += height + 15
            self._draw_centered(y, "Enter or Esc: Return to menu", HINT_COLOR)
            _, height = self.window.text_size("Enter or Esc: Return to menu")
            y += height + 10
        if message:
            self._draw_centered(y, message, ERROR_COLOR)
