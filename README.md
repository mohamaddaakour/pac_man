*This project has been created as part of the 42 curriculum by mdaakour, gmoujaes.*

# Pac-Man: Ghosts! More ghosts!

A Pac-Man project written in Python 3.10+. The current core generates a maze
and lets you play the first level in the terminal, collecting pellets for points.

## Current features

- JSON configuration with comments, safe defaults, and clear messages for bad values
- Maze generation using the assigned A-Maze-ing package
- Checks for connected corridors and valid starting positions
- Playable ASCII maze with WASD controls and buffered turns
- Normal and super-pacgum scoring using configured point values
- Level completion when all pellets are eaten

Ghost collisions, edible behavior, AI, timers, level progression, and highscores
are implemented in later core phases. The phase 3 demo uses stationary,
harmless ghosts; lives and the level timer do not decrease.

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
positions are distinct. Super-pacgums occupy the ghost spawn tiles. Normal pellets
occupy all other corridors except the player's starting tile.

The demo plays the first configured level: `#` is a wall, `.` is a normal pellet,
`O` is a super-pacgum, `P` is the player, and `1` to `4` are ghosts in corner
order. Ghost markers cover the super-pacgums at their starting positions.

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

# Same playable demo through the project entry point
python -m pacman.main config.json
```

## Phase 3 controls and scoring

Type `w`, `a`, `s`, or `d`, followed by Enter, to request a direction. Press Enter
alone to continue moving. Each accepted command advances 0.15 simulated seconds,
which moves the player one tile if the path is open. Time does not advance while
the terminal waits for input. Use `q`, Ctrl+C, or end-of-input to close the demo.
Invalid commands display help without advancing the game.

Walls stop movement. A blocked turn stays buffered: the player keeps moving
straight and turns at the first tile where the requested direction is possible.

Normal pellets award `points_per_pacgum`; super-pacgums award
`points_per_super_pacgum`. Each pellet is removed when eaten and scores only once.
Walking onto a ghost's starting tile collects its super-pacgum without losing a
life in this phase. Super-pacgums do not yet make ghosts edible.

When both pellet sets are empty, the core sets `status` to `level_won`, freezes
movement, and the demo prints a completion message and exits. Automatic progression
to the next level comes in phase 6.

## Check the code

```bash
python -m pytest -q tests
python -m flake8 .
python -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```
