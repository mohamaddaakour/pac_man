*This project has been created as part of the 42 curriculum by mdaakour, gmoujaes.*

# Pac-Man: Ghosts! More ghosts!

A Pac-Man project written in Python 3.10+. We can load the configuration, generate a maze, and display the player and ghost starting positions in the terminal.

## Current features

- JSON configuration with comments, safe defaults, and clear messages for bad values
- Maze generation using the assigned A-Maze-ing package
- Checks for connected corridors and valid starting positions
- ASCII preview of the maze in the terminal

Movement, ghost AI, scoring, highscores, and graphics are planned for later.

## Maze generation and spawns

We added `pacman/maze_adapter.py` to use the assigned
`mazegenerator-2.1.0` package without changing its code.

- `build_grid(width, height, seed)` calls `MazeGenerator` with
  `size=(width, height)` and `perfect=False`.
- We convert the package's wall masks into a grid where `0` means corridor
  and `1` means wall. Fully blocked cells, including the "42" pattern, stay walls.
- Width and height are generator cell counts, from 5 to 99. The tile grid has
  `2 * height + 1` rows and `2 * width + 1` columns.
- We validate the masks and walls. A breadth-first search (BFS) checks that
  every corridor is reachable.
- Failed generation is retried up to five times after the first attempt.
  If all six attempts fail, we raise `MazeError` with a clear message.
- Fixed seeds produce repeatable mazes. The sample configuration uses seed 42
  for level 1 and random seeds for later levels. Generation preserves Python's
  global random state.

In `pacman/entities.py`, positions use `(row, column)`. `Direction` provides
the four movement vectors, `Entity` stores a position and direction, and
`is_walkable()` checks whether a position is inside the grid and on a corridor.

`choose_spawns()` places the player on the corridor tile nearest the center.
It then picks four different corridor tiles near the top-left, top-right,
bottom-left, and bottom-right corners for the ghosts. All five starting
positions are distinct. The ghost positions also mark the future super-pacgum
locations; collectible storage comes later.

The demo previews the first configured level: `#` is a wall, `P` is the player,
and `1` to `4` are ghosts in corner order. Ghost markers cover the super-pacgum
markers (`O`) at the same positions. This is a static preview.

# Instructions

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
# Run the demo
python -m tools.cli_demo config.json

# Same preview through the project entry point
python -m pacman.main config.json
```

## Check the code

```bash
python -m pytest -q tests
python -m flake8 .
python -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```
