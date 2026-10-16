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
- Ghost collisions, life loss, entity respawns, and 2 seconds of grace
- Timed edible ghosts, ghost scoring, and eaten-ghost respawns
- Invisibility toggle and a graphical integration demo
- Moving ghosts with BFS chasing, random junction choices, and slower fleeing

Ghosts now move in phase 5, and normal contacts cost a life.
The level countdown, level progression, and highscores come in later core phases.
Power, grace, and ghost respawn timers are active now.

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
Edible ghosts use `e`; eaten ghosts are hidden until they respawn.

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

# Graphical demo: WASD without Enter, I toggles invisibility, Esc/Q quits
make graphical-demo
```

## Movement controls and scoring

Type `w`, `a`, `s`, or `d`, followed by Enter, to request a direction. Press Enter
alone to continue moving. Each accepted command advances 0.15 simulated seconds,
which moves the player one tile if the path is open. Time does not advance while
the terminal waits for input. Use `q`, Ctrl+C, or end-of-input to close the demo.
Invalid commands display help without advancing the game.

Walls stop movement. A blocked turn stays buffered: the player keeps moving
straight and turns at the first tile where the requested direction is possible.

Normal pellets award `points_per_pacgum`; super-pacgums award
`points_per_super_pacgum`. Each pellet is removed when eaten and scores only once.
Walking onto a ghost's starting tile consumes its super-pacgum before resolving
contact, making that ghost edible and allowing it to be eaten for points.

When both pellet sets are empty, the core sets `status` to `level_won`, freezes
movement, and the demo prints a completion message and exits. Automatic progression
to the next level comes in phase 6.

## Phase 4 collisions and invisibility

A normal ghost costs one life on contact unless invisibility or grace protects
the player. Multiple simultaneous contacts cost at most one life. Losing a life
resets the player and ghosts to their starting positions and clears movement and
power. Score and already eaten pellets remain unchanged. A surviving player gets
2 seconds of grace; losing the last life sets `game_over` and freezes movement.

Super-pacgums refresh power to `edible_duration` seconds. Active ghosts become
edible; eating one awards `points_per_ghost`, makes it inactive, and teleports it
to its corner. It returns after `ghost_respawn_time`, edible if power remains
and normal otherwise. Inactive ghosts cannot hurt the player or score again
until they return. A new power-up does not revive them early.

Use `i` followed by Enter in the terminal, or I in the graphical demo, to toggle
invisibility. This prevents normal-ghost damage while permitting pellet and
edible-ghost scoring. The HUD shows invisibility, power time, and grace time.
Timers advance in simulated seconds in the terminal and elapsed frame time in
the graphical demo. The invisibility command itself consumes no terminal time.

Edible ghosts are blue in the graphical demo. Eaten ghosts are hidden in both
demos. The terminal exits on game over; the graphical demo displays the result
until Esc or Q closes it. Same-tile and swapped-tile contacts are supported.
Lethal last-life contact takes
priority over consuming the final pellet.

## Phase 5 moving ghosts

All four ghosts use BFS corridor distances to chase the player's current tile.
At junctions they choose the shortest allowed move in a 70% branch and a random
allowed move otherwise. The random branch can also choose the shortest move.
Ghosts avoid reversing while another exit is available and can reverse at dead
ends. Edible ghosts choose the allowed neighbor farthest from the player by BFS
distance; the no-reversal rule can force them closer in a narrow corridor.

The player moves every 0.15 seconds, normal ghosts every 0.20 seconds, and edible
ghosts every 0.30 seconds. Each ghost has an independent movement clock. Eaten
ghosts wait for their respawn timer and start a fresh movement interval when they
return. Power changes and life-loss resets also restart movement intervals.

Ghosts move even when the player is stopped. The terminal advances both player
and ghost simulation time with each movement/Enter command; the graphical demo
advances continuously. Use I to observe pursuit while protected from damage.
The core checks a player's arrival contact before a ghost can move away and
shares one BFS distance map among ghosts due at the same event.

Ghost decisions use a separate random generator. A fixed level seed and the same
timed input sequence reproduce decisions within the same runtime; omitted seeds
request fresh randomness. Level progression and the level countdown remain for
phase 6.

## Check the code

```bash
python -m pytest -q tests
python -m flake8 .
python -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```
