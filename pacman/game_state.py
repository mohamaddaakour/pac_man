from __future__ import annotations

import math

from pacman.entities import Direction, Entity, choose_spawns, is_walkable
from pacman.maze_adapter import build_grid
from pacman.config import Config


class GameState:
    """All mutable state of a running game."""

    # Pac-Man moves one tile every 0.15 seconds.
    # Moving one tile per frame would make fast computers run the game faster.
    # Using time makes the speed the same everywhere.
    STEP_TIME = 0.15

    status: str  # "playing" | "level_won" | "game_won" | "game_over"

    score: int
    lives: int

    level: int  # 1-based

    time_left: float
    invisible: bool

    def __init__(self, config: Config) -> None:
        """Generate level 1 and place entities and points."""
        self.config = config
        self.status = "playing"
        self.score = 0
        self.lives = config.lives
        self.level = 1
        self.time_left = config.level_max_time
        self.invisible = False
        spec = config.levels[0]
        self.grid = build_grid(spec.width, spec.height, spec.seed)
        player_spawn, ghost_spawns = choose_spawns(self.grid)
        self.player_spawn = player_spawn
        self.ghost_spawns = ghost_spawns
        self.player = Entity(player_spawn)
        self.ghosts = [Entity(pos) for pos in ghost_spawns]
        self.next_direction: Direction | None = None
        self._movement_elapsed = 0.0

        self.super_pacgums = set(ghost_spawns)
        excluded = {player_spawn, *ghost_spawns}

        # Put the positions of pacgums
        self.pacgums = {
            (row, col)
            for row in range(len(self.grid))
            for col in range(len(self.grid[row]))
            if self.grid[row][col] == 0 and (row, col) not in excluded
        }

    def set_direction(self, direction: Direction) -> None:
        """Remember the requested turn until it becomes possible.
        It Stores the requested direction. It does not move anything.
        """
        self.next_direction = direction

    def update(self, dt: float) -> None:
        """Advance finite non-negative seconds; retain partial tile steps.

        Args:
            dt: Seconds elapsed since the last update.
        """

        if not math.isfinite(dt) or dt < 0:
            raise ValueError('dt must be finite and non-negative')

        if self.status != 'playing':
            return

        self._movement_elapsed += dt

        while self._movement_elapsed + 1e-12 >= self.STEP_TIME:
            self._movement_elapsed = max(
                0.0, self._movement_elapsed - self.STEP_TIME
            )

            self._move_one_tile()

            if self.status != 'playing':
                self._movement_elapsed = 0.0
                break

    def _move_one_tile(self) -> None:
        """Try a buffered turn, otherwise keep going straight or stop."""
        row, col = self.player.pos
        direction = self.next_direction

        if direction is not None:
            target = row + direction.dr, col + direction.dc
            if is_walkable(self.grid, target):
                self.player.direction = direction

        direction = self.player.direction

        if direction is None:
            return

        target = row + direction.dr, col + direction.dc

        if not is_walkable(self.grid, target):
            self.player.direction = None
            return

        self.player.pos = target

        self._eat_at_player()

    def _eat_at_player(self) -> None:
        """Remove a point, award its points once, and detect completion."""
        pos = self.player.pos

        if pos in self.pacgums:
            self.pacgums.remove(pos)
            self.score += self.config.points_per_pacgum
        elif pos in self.super_pacgums:
            self.super_pacgums.remove(pos)
            self.score += self.config.points_per_super_pacgum

        # If all pacgums and super pacgums are collected the level
        # will be ended and the player won this level
        if not self.pacgums and not self.super_pacgums:
            self.status = 'level_won'

    def toggle_invisibility(self) -> None:
        """Flip the cheat mode flag."""
        raise NotImplementedError

    def next_level(self) -> None:
        """Build the next level, keeping score and lives."""
        raise NotImplementedError
