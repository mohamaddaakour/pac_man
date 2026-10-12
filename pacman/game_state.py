from __future__ import annotations

import math

from pacman.entities import (
    Direction, Entity, Ghost, GhostState, Position, choose_spawns, is_walkable,
)
from pacman.maze_adapter import build_grid
from pacman.config import Config


EPSILON = 1e-12


def countdown(timer: float, dt: float) -> float:
    """Subtract elapsed seconds, snapping rounding residue to zero."""
    remaining = timer - dt

    return remaining if remaining > EPSILON else 0.0


class GameState:
    """All mutable state of a running game."""

    # Pac-Man moves one tile every 0.15 seconds.
    # Moving one tile per frame would make fast computers run the game faster.
    # Using time makes the speed the same everywhere.
    STEP_TIME = 0.15

    # After you lose a life, you’re protected for 2 seconds.
    GRACE_DURATION = 2.0

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
        self.edible_timer = 0.0
        self.grace_timer = 0.0
        spec = config.levels[0]
        self.grid = build_grid(spec.width, spec.height, spec.seed)
        player_spawn, ghost_spawns = choose_spawns(self.grid)
        self.player_spawn = player_spawn
        self.ghost_spawns = ghost_spawns
        self.player = Entity(player_spawn)
        self.ghosts = [Ghost(pos) for pos in ghost_spawns]
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

    def toggle_invisibility(self) -> None:
        """Toggle normal-ghost protection; edible ghosts still score."""
        self.invisible = not self.invisible

    def update(self, dt: float) -> None:
        """Advance finite non-negative seconds; retain partial tile steps.

        Args:
            dt: Seconds elapsed since the last update.
        """

        if not math.isfinite(dt) or dt < 0:
            raise ValueError('dt must be finite and non-negative')

        if self.status != 'playing':
            return

        old_player = self.player.pos
        old_ghosts = tuple(ghost.pos for ghost in self.ghosts)

        if self._resolve_collisions(old_player, old_ghosts):
            return

        remaining = dt

        while remaining > 0:
            deadlines = [self.STEP_TIME - self._movement_elapsed]

            deadlines.extend(timer for timer in (
                self.edible_timer, self.grace_timer,
                *(ghost.respawn_timer for ghost in self.ghosts),
            ) if timer > 0)

            elapsed = min(remaining, *deadlines)
            self._advance_timers(elapsed)
            self._movement_elapsed += elapsed
            remaining = max(0.0, remaining - elapsed)
            old_player = self.player.pos
            old_ghosts = tuple(ghost.pos for ghost in self.ghosts)

            if self._movement_elapsed + EPSILON >= self.STEP_TIME:
                self._movement_elapsed = 0.0
                self._move_one_tile()

            if self._resolve_collisions(old_player, old_ghosts):
                return

            if not self.pacgums and not self.super_pacgums:
                self.status = 'level_won'
                self._movement_elapsed = 0.0
                return

    def _advance_timers(self, dt: float) -> None:
        """Expire power/grace and return eaten ghosts to their corner state."""
        self.edible_timer = countdown(self.edible_timer, dt)
        self.grace_timer = countdown(self.grace_timer, dt)
        for ghost in self.ghosts:
            if ghost.state == GhostState.EATEN:
                ghost.respawn_timer = countdown(ghost.respawn_timer, dt)
                if ghost.respawn_timer == 0:
                    ghost.state = (
                        GhostState.EDIBLE if self.edible_timer > 0
                        else GhostState.NORMAL
                    )
            elif self.edible_timer == 0:
                ghost.state = GhostState.NORMAL

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
            self.edible_timer = self.config.edible_duration

            for ghost in self.ghosts:
                if ghost.state != GhostState.EATEN:
                    ghost.state = GhostState.EDIBLE

    def _resolve_collisions(
        self, old_player: Position, old_ghosts: tuple[Position, ...],
    ) -> bool:
        """Resolve shared or swapped tiles; return True after losing a life."""
        contacts = [
            (index, ghost) for index, (ghost, previous)
            in enumerate(zip(self.ghosts, old_ghosts))
            if ghost.state != GhostState.EATEN and (
                ghost.pos == self.player.pos or (
                    old_player == ghost.pos and self.player.pos == previous
                )
            )
        ]
        # A dangerous contact costs at most one life, even with several ghosts.
        if not self.invisible and self.grace_timer == 0 and any(
            ghost.state == GhostState.NORMAL for _, ghost in contacts
        ):
            self._lose_life()
            return True
        for index, ghost in contacts:
            if ghost.state == GhostState.EDIBLE:
                self.score += self.config.points_per_ghost
                ghost.state = GhostState.EATEN
                ghost.respawn_timer = self.config.ghost_respawn_time
                ghost.pos = self.ghost_spawns[index]
                ghost.direction = None
        return False

    def _lose_life(self) -> None:
        """Reset entities and power, preserving score and eaten pellets."""
        self.lives -= 1
        self.player.pos = self.player_spawn
        self.player.direction = None
        self.next_direction = None
        self._movement_elapsed = 0.0
        self.edible_timer = 0.0

        for ghost, spawn in zip(self.ghosts, self.ghost_spawns):
            ghost.pos = spawn
            ghost.direction = None
            ghost.state = GhostState.NORMAL
            ghost.respawn_timer = 0.0

        self.grace_timer = self.GRACE_DURATION

        if self.lives == 0:
            self.status = 'game_over'

    def next_level(self) -> None:
        """Build the next level, keeping score and lives."""
        raise NotImplementedError
