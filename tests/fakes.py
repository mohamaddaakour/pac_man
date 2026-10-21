"""Test doubles: fake window, fake game state and fake highscores."""

from __future__ import annotations

from dataclasses import dataclass, field

from pacman.entities import Direction, Entity, Ghost, Grid, Position


@dataclass
class FakeState:
    """Minimal game state matching frontend.protocols.GameStateProtocol.

    The methods only record what the frontend asked for, so tests can
    check the calls without running the real game.
    """

    grid: Grid
    player: Entity
    ghosts: list[Ghost]
    pacgums: set[Position] = field(default_factory=set)
    super_pacgums: set[Position] = field(default_factory=set)
    score: int = 0
    lives: int = 3
    level: int = 1
    total_levels: int = 10
    time_left: float = 90.0
    edible_timer: float = 0.0
    status: str = 'playing'
    invisible: bool = False
    updates: list[float] = field(default_factory=list)
    directions: list[Direction] = field(default_factory=list)
    next_level_calls: int = 0

    def update(self, dt: float) -> None:
        """Record one time step."""

        self.updates.append(dt)

    def set_direction(self, direction: Direction) -> None:
        """Record a requested turn."""

        self.directions.append(direction)

    def toggle_invisibility(self) -> None:
        """Flip the cheat flag."""

        self.invisible = not self.invisible

    def skip_level(self) -> None:
        """Win the level like the core does: the last one ends the game."""

        if self.status == 'playing':
            self.status = ('game_won' if self.level == self.total_levels
                           else 'level_won')

    def next_level(self) -> None:
        """Move to the next level."""

        self.next_level_calls += 1
        self.level += 1
        self.status = 'playing'


@dataclass
class FakeHighscores:
    """In-memory table matching frontend.protocols.HighscoresProtocol.

    `qualify` and `accept` let a test choose what qualifies() and add()
    answer, to reach every branch of the end screen.
    """

    entries: list[tuple[str, int]] = field(default_factory=list)
    qualify: bool = True
    accept: bool = True
    last_error: str | None = None

    def load(self) -> None:
        """Nothing to read."""

    def qualifies(self, score: int) -> bool:
        """Answer what the test asked for."""

        return self.qualify

    def add(self, name: str, score: int) -> bool:
        """Store the entry, or fail with a message if told to."""

        if not self.accept:
            self.last_error = 'Could not save the score'
            return False
        self.last_error = None
        self.entries.append((name, score))
        return True

    def top10(self) -> list[tuple[str, int]]:
        """Return the stored entries."""

        return list(self.entries)


def open_grid(rows: int, cols: int) -> Grid:
    """Return a grid with a wall border and corridors inside."""

    return [
        [1 if row in (0, rows - 1) or col in (0, cols - 1) else 0
         for col in range(cols)]
        for row in range(rows)
    ]


def make_state(rows: int = 7, cols: int = 7) -> FakeState:
    """Build a level laid out like the real core.

    The player is in the middle, the ghosts and super-pacgums are in the
    four inner corners, and every other corridor tile has a pacgum.
    """

    grid = open_grid(rows, cols)
    middle = (rows // 2, cols // 2)
    corners = [(1, 1), (1, cols - 2), (rows - 2, 1), (rows - 2, cols - 2)]
    pacgums = {
        (row, col)
        for row in range(rows) for col in range(cols)
        if grid[row][col] == 0 and (row, col) not in {middle, *corners}
    }

    return FakeState(
        grid=grid,
        player=Entity(middle),
        ghosts=[Ghost(pos) for pos in corners],
        pacgums=pacgums,
        super_pacgums=set(corners),
    )
