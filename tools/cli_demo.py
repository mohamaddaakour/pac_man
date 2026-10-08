"""Terminal demo of the game core."""

from __future__ import annotations

import sys

from pacman.config import ConfigError, load_config
from pacman.entities import (
    Grid,
    Position,
    choose_spawns,
)
from pacman.maze_adapter import MazeError, build_grid


def render_ascii(
    grid: Grid,
    player: Position,
    ghosts: tuple[Position, ...],
) -> str:
    """Render walls and spawns; ghosts cover their super-pacgums."""

    canvas = [
        ['#' if tile else ' ' for tile in row]
        for row in grid
    ]

    # Super-pacgums
    for row, col in ghosts:
        canvas[row][col] = 'O'

    # Ghosts cover the super-pacgums initially.
    for number, (row, col) in enumerate(
        ghosts,
        start=1,
    ):
        canvas[row][col] = str(number)

    player_row, player_col = player
    canvas[player_row][player_col] = 'P'

    return '\n'.join(
        ''.join(row)
        for row in canvas
    )


def main(argv: list[str]) -> int:
    """Run the terminal demo."""

    if len(argv) > 1:
        path = argv[1]
    else:
        path = "config.json"

    try:
        config = load_config(path)

        level = config.levels[0]

        grid = build_grid(
            level.width,
            level.height,
            level.seed,
        )

        player, ghosts = choose_spawns(grid)

    except (ConfigError, MazeError) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    print("Resolved configuration:")

    for field, value in vars(config).items():
        print(f"{field}: {value}")

    print(
        f"\nTile grid: {len(grid)} rows "
        f"x {len(grid[0])} columns"
    )

    print(
        f"Player: {player}; corners: {ghosts}"
    )

    print(
        render_ascii(
            grid,
            player,
            ghosts,
        )
    )

    print(
        "Legend: # wall, P player, "
        "1–4 ghosts (TL, TR, BL, BR)"
    )

    print(
        "Each ghost covers a super-pacgum O "
        "at its starting position."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))