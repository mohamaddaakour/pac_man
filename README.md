*This project has been created as part of the 42 curriculum by mdaakour, gmoujaes.*

# Pac-Man: Ghosts! More ghosts!

A Pac-Man project written in Python 3.10+. Play a campaign of generated mazes
in the terminal or a graphical demo, collecting pellets and avoiding ghosts.
Both applications provide a menu, instructions, name entry, and saved highscores.

## Description

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
- A campaign of at least ten levels with countdowns and win/lose outcomes
- Pause/resume and level transitions that preserve score and lives
- Menus, instructions, and persistent top-ten highscores with name validation

Normal ghost contacts and level timeouts cost a life. Power, grace, and ghost
respawn timers are active during play. Completed games can enter the persistent
top-ten table; scores are saved only after a valid name is submitted.

## Maze generation and spawns

`pacman/maze_adapter.py` uses the assigned
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

The terminal map uses `#` for walls and `.` for normal pellets.
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

The required root entry point accepts exactly one JSON config filename:

```bash
python3 pac-man.py config.json
```

Alternative launch commands:

```bash
# Terminal menu and campaign
python -m tools.cli_demo config.json

# Same playable demo through the project entry point
python -m pacman.main config.json

# Graphical menu and campaign
make graphical-demo
```

## Movement controls and scoring

Type `w`, `a`, `s`, or `d`, followed by Enter, to request a direction. Press Enter
alone to continue moving. Each accepted command advances 0.15 simulated seconds,
which moves the player one tile if the path is open. Time does not advance while
the terminal waits for input. Q returns from play to the menu; Q at the menu
exits. Ctrl+C or end-of-input also closes the terminal application.
Invalid commands display help without advancing the game.

Walls stop movement. A blocked turn stays buffered: the player keeps moving
straight and turns at the first tile where the requested direction is possible.

Normal pellets award `points_per_pacgum`; super-pacgums award
`points_per_super_pacgum`. Each pellet is removed when eaten and scores only once.
Walking onto a ghost's starting tile consumes its super-pacgum before resolving
contact, making that ghost edible and allowing it to be eaten for points.

When both pellet sets are empty, a non-final level sets `status` to `level_won`
and freezes the core. Press N to continue. Clearing the final level sets
`game_won`. Either final outcome offers name entry if the score qualifies, then
returns to the menu. Quitting an unfinished game does not submit a score.

## Collisions and invisibility

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
demos. Both applications show the final score and offer eligible name entry. Same-tile and swapped-tile contacts are supported.
Lethal last-life contact takes priority over level completion.

## Ghost movement

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
request fresh randomness.

## Campaign, countdown, and pause

The campaign includes every configured level and extends shorter lists to at
least ten levels. If the first level omits its seed, it defaults to 42. Appended
levels use random seeds and grow by two generator cells per side up to 21.
Larger configured dimensions are preserved, and explicit seeds are honored.

Each level starts with `level_max_time` seconds. Ghost damage keeps the remaining
level time. A timeout costs one life, resets positions and the timer, and preserves
the maze, score, and already eaten pellets. Invisibility does not protect against
timeout. The last life lost sets `game_over` and freezes the core. A timeout that
coincides with a movement step takes precedence over that step.

Press P to pause or resume. Movement and all core timers freeze while paused.
Use N after clearing a level to generate the next maze. Score, lives, and
invisibility carry forward; pellets, power, movement clocks, and the level timer
reset. The graphical demo rebuilds its layout and cached walls for the new maze.
Generation failures display an error and exit with a failure code.

In the terminal, press Enter after each command. Time advances only with accepted
movement/Enter commands, and waiting for input consumes no time. The graphical
demo advances continuously and accepts keys without Enter. While paused, P
resumes and Q returns to the menu; other controls do not change the core.

The default 90-second limit can be tight for larger mazes. Set `level_max_time`
to 300 seconds or more when verifying a full campaign, then tune it for the
configured dimensions and desired difficulty.

| Control | Action |
|---|---|
| WASD | Request a movement direction |
| Enter (terminal) | Continue moving and advance simulated time |
| I | Toggle invisibility during active play |
| P | Pause/resume |
| N | Advance a cleared non-final level |
| Q / Esc (graphical) | Return to menu; quit from the menu |

## Menu and score entry

At the menu, S or Enter starts a new campaign, H displays highscores, T shows
instructions, and Q exits. In the graphical application, any key returns from
instructions or the score table to the menu. A new game resets gameplay state.

After a win or loss, submit 1–10 ASCII letters, digits, or spaces. Names containing
only spaces are rejected. In the terminal, an empty name skips submission; in the
window, Backspace edits, Enter saves, and Escape skips. Invalid names or save
failures can be corrected/retried. A successful submission happens once and is
shown in the score table. Games played with invisibility remain eligible.

## Configuration

JSON supports full-line # comments, // line comments, and /* block comments */.
Comment-like text inside strings is preserved. Missing/invalid values use defaults
or clamps with a message; unknown keys are ignored. Invalid files raise a readable
ConfigError. A UTF-8 BOM is accepted.

| Key | Default | Accepted values |
|---|---|---|
| highscore_filename | highscores.json | Nonempty path; relative to the config directory |
| levels | One 15×15 level, seed 42 | List of width/height/optional seed objects |
| Level width/height | 15 | Integers clamped to 5–99 generator cells |
| Level seed | Random when omitted | Integer or null; campaign's first default becomes 42 |
| lives | 3 | Integer, 1–9 |
| points_per_pacgum | 10 | Integer, 0–10000 |
| points_per_super_pacgum | 50 | Integer, 0–10000 |
| points_per_ghost | 200 | Integer, 0–10000 |
| level_max_time | 90 | Number, 10–3600 seconds |
| edible_duration | 10 | Number, 1–60 seconds |
| ghost_respawn_time | 5 | Number, 1–60 seconds |

Booleans are not accepted as numeric values. Absolute score paths are honored;
relative paths are resolved beside the supplied config file, independent of the
launch directory. The core keeps Config immutable when expanding the campaign.

## Highscores

Highscores keeps at most ten [name, score] pairs in a JSON list, sorted by score
in descending order. Scores must be non-negative integers, excluding booleans.
When the table is full, a new score must exceed the last score. Equal scores keep
their existing order. top10() returns a copy.

JSON is easy to inspect and requires no additional database dependency. The
manager validates every loaded entry, ignores malformed rows, and uses an empty
table with a warning for unreadable or corrupt files. Missing files start empty.
It writes a temporary file in the destination directory, flushes/synchronizes it,
then replaces the target atomically. A failed save returns False, preserves the
previous in-memory table and existing file, and exposes last_error for the UI.
The application must have permission to write to the selected directory.

The manager is intended for a single running application; simultaneous writers
are not coordinated with a file lock.

## General software architecture

- pacman/config.py validates settings and provides immutable data classes.
- pacman/maze_adapter.py isolates the assigned generator and validates tile grids.
- pacman/entities.py defines directions, positions, entities, and spawn helpers.
- pacman/ghost_ai.py computes corridor distances and chase/flee decisions.
- pacman/levels.py expands the campaign; pacman/game_state.py owns all game rules.
- pacman/highscore.py owns validation, ranking, and atomic persistence.
- tools/session.py resolves score storage and formats score tables.
- tools/cli_demo.py and tools/graphical_demo.py own menus, input, pause, and display.
- frontend/window.py provides the graphical window and image API. Other frontend
  modules remain the teammate's integration work.

See [the core API contract](docs/core-api.md) for the frontend handoff. Rendering
reads state; it never removes pellets, awards points, or advances timers itself.

## Implementation

The core uses timed tile steps and event boundaries for player movement, ghost
movement, and timer expirations. Player arrival contact is checked before a ghost
can move away. The window caches static walls and sprites, rebuilding them when
the level grid changes. Both applications keep application flow separate from
GameState. Unexpected application errors return a failure code without a traceback.

## Project management

Progress and team organization are tracked in [docs/project_management](docs/project_management).
The [acceptance checklist](docs/project_management/acceptance.md) and
[risk notes](docs/project_management/risks.md) cover the core handoff. Documentation
records implementation and manual/runtime checks separately from unit testing.

## Resources

- [Python JSON documentation](https://docs.python.org/3/library/json.html)
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html)
- [Python tempfile documentation](https://docs.python.org/3/library/tempfile.html)
- [Pygame documentation](https://www.pygame.org/docs/)
- The assigned mazegenerator wheel's source and metadata document its actual API.

AI assistance was used for roadmap planning, implementation suggestions, bug
reviews, integration, runtime verification, and documentation. The original
structure of the highscore manager was retained when applying fixes.

## Check the code

```bash
python -m pytest -q tests
python -m flake8 .
python -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```
