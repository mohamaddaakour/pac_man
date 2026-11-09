*This project has been created as part of the 42 curriculum by mdaakour, gmoujaes.*

# Pac-Man: Ghosts! More ghosts!

A Pac-Man game written in Python 3.10+. Play a campaign of at least ten
generated mazes in a pygame window that uses only MLX-equivalent calls, with a
main menu, instructions, a pause menu, and a persistent top-ten highscore table.
A standalone Linux build is published on itch.io.

## Description

The goal is to clear every level: eat all the pacgums of each maze before the
timer runs out, without losing your last life. Super-pacgums make the ghosts
edible for a few seconds, so Pac-Man can eat them for extra points.

- JSON configuration with comments, safe defaults, and clear messages for bad values
- Maze generation using the assigned A-Maze-ing package
- Checks for connected corridors and valid starting positions
- Arrow-key and WASD movement with buffered turns
- Normal and super-pacgum scoring using configured point values
- Level completion when all pellets are eaten
- Ghost collisions, life loss, entity respawns, and 2 seconds of grace
- Timed edible ghosts, ghost scoring, and eaten-ghost respawns
- Moving ghosts with BFS chasing, random junction choices, and slower fleeing
- A campaign of at least ten levels with countdowns and win/lose outcomes
- Pause/resume and level transitions that preserve score and lives
- Cheats for reviewers: invisibility (I) and level skip (K)
- Menus, instructions, and persistent top-ten highscores with name validation
- A standalone Linux package, published on itch.io

Normal ghost contacts and level timeouts cost a life. Power, grace, and ghost
respawn timers are active during play. Completed games can enter the persistent
top-ten table; scores are saved only after a valid name is submitted.

## Instructions

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
make install    # python -m pip install -r requirements.txt
```

`requirements.txt` installs the assigned maze generator wheel, pygame 2.6.1,
PyInstaller 6.22.3, and the check tools (flake8, mypy, pytest).

### Run

The required root entry point accepts exactly one JSON config filename:

```bash
python3 pac-man.py config.json
make run                              # the same, with config.json
make run CONFIG=configs/large.json    # another configuration
```

The filename has no required extension: `python3 pac-man.py settings.txt` also
works when the file contains valid JSON with the supported comments.
It opens the game window. Wrong arguments print a usage line, and other expected
problems (an invalid config, missing pygame, no display) print one `Error:`
line; both exit with code 1. Ctrl+C exits with 130. No traceback is shown.
To play without Python installed,
use the [Linux package](#linux-package).

`configs/` holds ready-made configurations for manual checks: `scoring.json`
(1, 10 and 100 points), `timeout.json` (10-second levels), `large.json` (every
level 99×99), and `shapes.json` (5×5, 99×5, 5×99, and 99×99 mazes).

### Controls

| Where | Keys |
| --- | --- |
| Menus | Up/Down or W/S choose, Enter selects, Esc goes back (on the main menu, Esc quits) |
| Playing | Arrow keys or WASD move; P or Esc pauses |
| Pause menu | Up/Down choose RESUME or MAIN MENU, Enter selects; P or Esc resumes |
| Cheats | I toggles invisibility (ghosts cannot take lives); K skips the level without points |
| End of game | Type a name (1–10 letters, digits, or spaces), Backspace erases, Enter saves, Esc skips |
| Anywhere | The window's close button quits |

WASD is read by key position, so AZERTY keyboards use ZQSD. The Instructions
screen lists the controls and the values loaded from the config.

### Linux package

The game can be packaged as a standalone Linux build that runs without Python.

#### Build

```bash
make install    # installs PyInstaller with the other requirements
make package
```

`make package` runs `package.sh`. The script deletes any old `build/` and
`dist/` folders, builds the game with PyInstaller from `pac-man.spec`, and
assembles the package. It takes about 10 seconds.

#### Output

| Path | Content |
| --- | --- |
| `dist/pac-man-linux.tar.gz` | The archive to share or upload (about 30 MB) |
| `dist/pac-man-linux/` | The same package, already extracted |

```
pac-man-linux/
├── run.sh            launcher
├── config.json       editable settings; scores are saved next to it
├── INSTRUCTIONS.txt  controls, options and configuration keys
├── CREDITS.txt       authors and licences
└── pac-man/          the game, with Python and pygame included
```

#### Launch

```bash
tar -xzf pac-man-linux.tar.gz
cd pac-man-linux
sh run.sh             # plays with config.json from this folder
sh run.sh my.json     # or with another configuration file
```

`run.sh` works from any folder. Scores are saved in `highscores.json` next to
the configuration file. The same archive is published on itch.io as a
restricted page.

#### Requirements

- 64-bit (x86_64) Linux with glibc 2.35 or newer, such as Ubuntu 22.04 or newer.
- A graphical desktop session: X11, or Wayland with XWayland (Ubuntu's default).
- No Python, pygame or other installation is needed.

The package is built on Ubuntu 22.04. A PyInstaller build runs only on systems
whose glibc is at least as new as the build machine's, so build on the oldest
system you want to support. The package was tested by playing a full game in a
bare `ubuntu:22.04` container with no Python installed.

### Check the code

```bash
make test           # python -m pytest -q tests
make lint           # flake8 and mypy with the subject's flags
make lint-strict    # flake8 and mypy --strict
```

Without Make:

```bash
python -m pytest -q tests
python -m flake8 .
python -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

Install `requirements.txt` into the interpreter used for these commands.
On Windows, activate with `.venv\Scripts\Activate.ps1`, or invoke
`.venv\Scripts\python.exe` directly. GNU Make is optional for running the
equivalent commands above. See [the test guide](docs/pytest.md) for the core
tests and [the acceptance record](docs/project_management/acceptance.md) for
results. The frontend tests run without a display (see
[Frontend decisions](#frontend-decisions)).

## Maze Generation

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
- Level 1 uses a fixed seed (42 when omitted); every later campaign level uses
  a random seed, even if its config entry supplies one. Direct adapter calls
  with a fixed seed remain repeatable. Generation preserves Python's global
  random state.

In `pacman/entities.py`, positions use `(row, column)`. `Direction` provides
the four movement vectors, `Entity` stores a position and direction, and
`is_walkable()` checks whether a position is inside the grid and on a corridor.

`choose_spawns()` places the player on the corridor tile nearest the center.
It then picks four different corridor tiles near the top-left, top-right,
bottom-left, and bottom-right corners for the ghosts. All five starting
positions are distinct. Super-pacgums occupy the ghost spawn tiles. Normal pellets
occupy all other corridors except the player's starting tile.

The game window draws the "42" pattern in green. The terminal map uses `#` for
walls and `.` for normal pellets. `O` is a super-pacgum, `P` is the player, and
`1` to `4` are ghosts in corner order. Ghost markers cover the super-pacgums at
their starting positions. Edible ghosts use `e`; eaten ghosts are hidden until
they respawn.

## Movement and scoring

In the game window, the arrow keys or WASD request a direction and the game
runs in real time. In the terminal, type `w`, `a`, `s`, or `d`, followed by
Enter, to request a direction. Press Enter alone to continue moving. Each
accepted command advances 0.15 simulated seconds, which moves the player one
tile if the path is open. Time does not advance while the terminal waits for
input. Q returns from play to the menu; Q at the menu exits. Ctrl+C or
end-of-input also closes the terminal application. Invalid commands display
help without advancing the game.

Walls stop movement. A blocked turn stays buffered: the player keeps moving
straight and turns at the first tile where the requested direction is possible.

Normal pellets award `points_per_pacgum`; super-pacgums award
`points_per_super_pacgum`. Each pellet is removed when eaten and scores only once.
Walking onto a ghost's starting tile consumes its super-pacgum before resolving
contact, making that ghost edible and allowing it to be eaten for points.

When both pellet sets are empty, a non-final level sets `status` to `level_won`
and freezes the core. The game window then shows "LEVEL n/10" for 2 seconds and
starts the next maze; the terminal waits for N. Clearing the final level sets
`game_won`. Both versions ask for a name after either final outcome, then return
to the menu. A score outside the top ten is not saved, and a message says so.
Quitting an unfinished game submits nothing.

## Collisions and invisibility

A normal ghost costs one life on contact unless invisibility or grace protects
the player. Multiple simultaneous contacts cost at most one life. Losing a life
resets the player and ghosts to their starting positions and clears movement and
power. Score and already eaten pellets remain unchanged. A surviving player gets
2 seconds of grace; losing the last life sets `game_over` and freezes movement.

Super-pacgums refresh power to `edible_duration` seconds. Active ghosts become
edible; eating one awards `points_per_ghost`, makes it inactive, and teleports it
to its corner. It returns as NORMAL after `ghost_respawn_time`, even if the
previous power timer remains active. Another super-pacgum can make it edible
again. Inactive ghosts cannot hurt the player or score again until they return.
A new power-up does not revive them early.

Press I in the game window, or `i` followed by Enter in the terminal, to toggle
invisibility. This prevents normal-ghost damage while permitting pellet and
edible-ghost scoring. The window's HUD shows INVISIBLE while it is on; the
terminal HUD also shows the power and grace times. Timers advance with elapsed
frame time in the window and in simulated seconds in the terminal. The
invisibility command itself consumes no terminal time.

In the window, edible ghosts are blue and blink white during their last 2
seconds, and an eaten ghost is drawn as eyes only until it respawns. Both
versions show the final score. Same-tile and swapped-tile contacts are supported.
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
and ghost simulation time with each movement/Enter command; the game window
advances continuously. Use I to observe pursuit while protected from damage.
The core checks a player's arrival contact before a ghost can move away and
shares one BFS distance map among ghosts due at the same event.

Ghost decisions use a separate random generator. A fixed level seed and the same
timed input sequence reproduce decisions within the same runtime; omitted seeds
request fresh randomness.

## Campaign, countdown, and pause

The campaign includes every configured level and extends shorter lists to at
least ten levels. The first level uses its configured seed, defaulting to 42.
Every later level uses fresh randomness. Appended levels grow by two generator
cells per side up to 21, without shrinking larger configured dimensions.
`GameState.total_levels` exposes the expanded count for the HUD's LEVEL 3/10.

Each level starts with `level_max_time` seconds. Ghost damage keeps the remaining
level time. A timeout costs one life, resets positions and the timer, and preserves
the maze, score, and already eaten pellets. Invisibility does not protect against
timeout. The last life lost sets `game_over` and freezes the core. A timeout that
coincides with a movement step takes precedence over that step.

Press P (or Esc in the window) to pause. Movement and all core timers freeze
while paused. After a cleared level, the next maze is generated: the window does
it before its "LEVEL n/10" screen, and the terminal when N is pressed. Score,
lives, and invisibility carry forward; pellets, power, movement clocks, and the
level timer reset. The window rebuilds its layout and images for the new maze.
If a maze cannot be generated, the window returns to the menu with the error,
and the terminal exits with a failure code.

K calls `skip_level()`: an active non-final level becomes `level_won`, or the
final level becomes `game_won`. It awards no points and preserves lives.
Skipping is ignored while paused or outside active play.

In the terminal, press Enter after each command. Time advances only with accepted
movement/Enter commands, and waiting for input consumes no time. While paused,
P resumes and Q returns to the menu; other controls do not change the core. The
window's pause menu offers RESUME and MAIN MENU.

The default 90-second limit can be tight for larger mazes. Set `level_max_time`
to 300 seconds or more when verifying a full campaign, then tune it for the
configured dimensions and desired difficulty.

Terminal controls (the window's are in [Controls](#controls)):

| Command | Action |
|---|---|
| w, a, s, d | Request a movement direction |
| Enter | Continue moving and advance simulated time |
| i | Toggle invisibility during active play |
| k | Win the active level immediately without extra points |
| p | Pause/resume |
| n | Advance a cleared non-final level |
| q | Return to menu; quit from the menu |

## Menu and score entry

The window's menu lists START GAME, VIEW HIGHSCORES, INSTRUCTIONS, and EXIT,
with the five best scores below. Enter or Esc returns from the instructions and
the score table. In the terminal, S or Enter starts a new campaign, H displays
highscores, T shows instructions, and Q exits. A new game resets gameplay state.

After a win or loss, submit 1–10 ASCII letters, digits, or spaces. Names containing
only spaces are rejected. In the terminal, an empty name skips submission; in the
window, Backspace edits, Enter saves, Escape skips, and characters a name cannot
contain are ignored as they are typed. Invalid names or save failures can be
corrected/retried. A successful submission happens once and is shown in the
score table. Games played with invisibility remain eligible.
Level-skip games also remain eligible; skipping itself contributes no score.

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
| Level seed | 42 for level 1; random later | Integer or null; explicit seeds apply only to level 1 during a campaign |
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

## Highscore

Highscores keeps at most ten [name, score] pairs in a JSON list, sorted by score
in descending order. Scores must be non-negative integers, excluding booleans.
When the table is full, a new score must exceed the last score. Equal scores keep
their existing order. top10() returns a copy.

JSON is easy to inspect and requires no additional database dependency. The
manager validates every loaded entry, ignores malformed rows, and uses an empty
table with a warning for missing, empty, unreadable, or corrupt files.
It writes a temporary file in the destination directory, flushes/synchronizes it,
then replaces the target atomically. A failed save returns False, preserves the
previous in-memory table and existing file, and exposes last_error for the UI.
The application must have permission to write to the selected directory.

The table is loaded when the game starts and saved when a name is submitted.
The window shows the five best scores in the main menu and the full top ten on
its highscores screen; a save error is shown on the end screen.

The manager is intended for a single running application; simultaneous writers
are not coordinated with a file lock.

## General Software Architecture

Core (`pacman/`, Dev A):

- pacman/config.py validates settings and provides immutable data classes.
- pacman/maze_adapter.py isolates the assigned generator and validates tile grids.
- pacman/entities.py defines directions, positions, entities, and spawn helpers.
- pacman/ghost_ai.py computes corridor distances and chase/flee decisions.
- pacman/levels.py expands the campaign; pacman/game_state.py owns all game rules.
- pacman/highscore.py owns validation, ranking, and atomic persistence.
- tools/session.py resolves score storage and formats score tables.

See [the core API contract](docs/core-api.md) for the frontend handoff. Rendering
reads state; it never removes pellets, awards points, or advances timers itself.

Graphical game (`pac-man.py` and `frontend/`, Dev B):

```
pac-man.py               checks the argument, loads the config and scores, opens the window
└── frontend/app.py      App: the screen state machine; owns the game, screens and renderer
    ├── input_handler.py key -> Action, name typing                          (pure)
    ├── screens.py       menu, instructions, highscores, pause, level change, end
    ├── renderer.py      maze, dots, ghosts, Pac-Man, HUD
    │   ├── layout.py    tile size and maze position                         (pure)
    │   └── sprites.py   sprite pixels                                       (pure)
    ├── protocols.py     what the frontend reads from the core               (pure)
    └── window.py        Window: images, text, key/close/frame hooks, loop (the only pygame import)
```

- `pac-man.py` builds the `Config` and `Highscores` from the core, opens a
  `Window`, and runs an `App` inside it.
- `App` receives the window's key and frame hooks. It creates a `GameState` for
  each game, calls `update(dt)` while playing, and asks `Renderer` or `Screens`
  to draw the current mode.
- `Renderer` and `Screens` read the game only through `GameStateProtocol` and
  `HighscoresProtocol`, and draw only through `Window`. `constants.py` holds the
  window size, colours, and timings.
- The core never imports `frontend/`, and only `frontend/window.py` imports pygame.

## Implementation

The core uses timed tile steps and event boundaries for player movement, ghost
movement, and timer expirations. Player arrival contact is checked before a ghost
can move away. The window and the terminal keep application flow separate from
GameState. Unexpected application errors return a failure code without a traceback.

### pygame used like MLX

Subject IV allows a library "similar to MLX": every function used must have an
MLX equivalent. `frontend/window.py` wraps pygame in an MLX-shaped `Window` and
uses only these calls:

| pygame call | MLX equivalent |
| --- | --- |
| `pygame.display.init()`, `pygame.font.init()` | `mlx_init` |
| `pygame.display.get_driver()` (detects a missing display) | `mlx_init` returning NULL |
| `pygame.display.set_mode((w, h))`, `pygame.display.set_caption(title)` | `mlx_new_window` |
| `pygame.image.frombuffer(bytearray, (w, h), "RGBX" or "RGBA")` | `mlx_new_image` + `mlx_get_data_addr` |
| `screen.blit(image, (x, y))`, only onto the window | `mlx_put_image_to_window` |
| `screen.fill(colour)`, only to clear the window | `mlx_clear_window` |
| `pygame.font.Font(None, 24)` once, then `font.render(text, False, colour)` + `blit` | `mlx_string_put` |
| `.get_size()` and `pygame.image.tobytes(..., "RGBA")` on rendered text | reading a text image's size and pixels |
| `pygame.event.get()`: `KEYDOWN` | `mlx_key_hook` |
| `pygame.event.get()`: `QUIT` | `mlx_hook(win, 17, ...)` (close button) |
| `pygame.key.set_repeat(delay, interval)` | `mlx_do_key_autorepeaton` / `off` |
| `pygame.display.flip()` | `mlx_do_sync` |
| `Window.run()`: polls events, calls the hooks | `mlx_loop` + `mlx_loop_hook` |
| `pygame.quit()` | `mlx_destroy_window` + `mlx_destroy_display` |

Key codes come from pygame's `K_*` and `KSCAN_*` constants, the counterparts of
MLX key codes. Time uses Python's `time.monotonic()` and `time.sleep()`. Nothing
else from pygame is used: no `draw`, `transform`, `mixer`, `time`, `sprite`,
`mouse`, or `Rect` helpers, and no `convert()`. Both self-audit commands print
nothing:

```bash
grep -rn --include='*.py' --exclude-dir=.venv -E "import pygame|from pygame" . | grep -v -E "frontend/window.py|tests/"
grep -rn --include='*.py' --exclude-dir=.venv -E "pygame\.(draw|transform|mixer|time|sprite|mouse|surfarray|Rect)|get_pressed|convert_alpha|\.convert\(\)" .
```

### Frontend decisions

Graphics:

- **pygame instead of MLX42.** MLX42's Python binding has no key hook, close
  hook, or text function. pygame needs no native build, raises Python
  exceptions instead of crashing, has type hints for mypy, and PyInstaller
  bundles it.
- **One door to pygame.** Only `window.py` imports it. Every other frontend
  module is plain Python, testable without a display.
- **Every shape is drawn pixel by pixel.** Pac-Man, the ghosts, their eyes, and
  the dots are computed into bytearrays, and titles are enlarged in Python,
  because pygame's shape and scaling helpers have no MLX equivalent. For the
  same reason, the game has no sound.
- **Build once, draw every frame.** When the maze changes, its background
  (walls, corridors, dots) and its sprites are built once. Each frame clears the
  window, then draws the background, the ghosts, Pac-Man, and the HUD, like
  MiniLibX. An eaten dot is painted over in the background instead of rebuilding it.
- **Two pixel formats.** The large background is opaque `RGBX` (a full-window
  image takes about 0.3 ms to draw as `RGBX` and 6.4 ms as `RGBA`); sprites,
  text, and the pause panel are `RGBA` for transparency.
- **Fixed 1200×900 window, scaled maze.** The tile is the largest size that
  fits below the 60 px HUD, at most 48 px, and the maze is centred: 27 px tiles
  at 15×15, 4 px at 99×99, any width and height mix. Resizable windows need
  `set_mode` flags with no MLX equivalent.
- **About 60 frames per second without `pygame.time`.** `Window.run()` measures
  each frame with `time.monotonic()`, sleeps for the rest of 1/60 s, and caps
  the elapsed time at 0.1 s so a slow frame cannot make entities jump.

Game flow:

- **Seven screens, one state machine.** `App.mode` is MENU, INSTRUCTIONS,
  HIGHSCORES, LEVEL_TRANSITION, PLAYING, PAUSED, or GAME_END; the mode decides
  what a key does and what is drawn.
- **Pausing means not calling `update`.** The core's timers freeze because they
  are not advanced, and the frozen game stays visible under the pause menu.
- **Automatic level change.** After a cleared level, "LEVEL n/10" is shown over
  the new maze for 2 seconds, then play resumes.
- **A name prompt after every game,** win or loss, as the subject asks. A score
  outside the top ten returns to the menu with "Not in the top 10: score not
  saved". A save error stays on the end screen, so the player can retry or skip.
- **The core contract is a `Protocol`.** The frontend reads the game through the
  read-only properties of `GameStateProtocol`, and mypy checks the real
  `GameState` against it. The frontend cannot change the game by mistake, and
  both halves were built in parallel with fakes.

Input:

- **Keys become actions.** `translate()` turns a key into an `Action` (UP,
  CONFIRM, BACK, PAUSE, ...) and each mode decides what it means. Arrows and
  commands are read by key code; WASD is read by scan code, the key's position.
- **No input queue.** `Window.run()` dispatches every key at the start of a
  frame, before the frame hook, so `App` handles each key at once in the key
  hook. The order stays deterministic, and tests simply call `on_key`.
- **Typing a name.** On the end screen, keys go to the name entry, so P, I,
  and K type letters. Key repeat is on only while typing a name.

Display:

- **HUD above the maze, in five fixed slots:** lives (with a Pac-Man icon),
  score, level, time, and INVISIBLE (cyan, while the cheat is on). It spans the
  maze width, at least 750 px, so it stays aligned with every maze shape. The
  time is rounded up and turns red in the last 10 seconds.
- **The 42 is visible.** Walls surrounded by walls on all eight sides are the
  generator's closed "42" cells; they are drawn green.
- **Ghosts always have eyes.** Each ghost has its own colour, edible ghosts are
  blue and blink white in their last 2 seconds, and an eaten ghost shows only
  its eyes. Pac-Man's mouth opens and closes while it moves.

Errors and tests:

- **Errors are handled in layers, never with a traceback.** `pac-man.py` turns
  each expected failure into one line and exit code 1: wrong arguments (usage
  line), a config error, missing pygame ("run make install"), no display
  ("cannot open the game window"), or a system error. Ctrl+C exits with 130,
  and anything unexpected prints one line. A maze that cannot be generated
  returns to the menu with the message. `pygame.quit()` always runs, in a `finally`.
- **Tests need no screen.** `tests/conftest.py` selects SDL's dummy video
  driver, so the window, renderer, and screens are tested with real pygame and
  checked pixel by pixel. `tests/fakes.py` provides a fake window, game, and
  score table for the app tests, and `tests/test_integration.py` plays with the
  real core.

Packaging:

- **A PyInstaller folder in a `tar.gz`,** with `run.sh`, `config.json`,
  `INSTRUCTIONS.txt`, and `CREDITS.txt` beside it. It starts at once (nothing
  is unpacked at launch), players can edit the config and find their scores
  next to it, and `tar.gz` keeps the executable bits. It is built on Ubuntu
  22.04 so it runs on glibc 2.35 or newer, and the pinned versions rebuild the
  same package during the review.

## Project Management

The work was split in two halves: Dev A (mdaakour) built the game core and
persistence, and Dev B (gmoujaes) the graphical frontend and the Linux package.
Each task has its own feature branch, merged into `main` after review by the
other developer. The
[project management folder](docs/project_management) holds:

- [timeline.md](docs/project_management/timeline.md): planned and actual dates
  and the status of every task;
- [team_organization.md](docs/project_management/team_organization.md): roles,
  workflow, the decision log, and blocking points;
- [acceptance.md](docs/project_management/acceptance.md): core, graphical, and
  package acceptance results;
- [risks.md](docs/project_management/risks.md): core risks and their handling;
- [dev-a-handoff.md](docs/project_management/dev-a-handoff.md): maps A1–A11 to
  their implementation and tests.

## Resources

- [Python JSON documentation](https://docs.python.org/3/library/json.html)
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html)
- [Python tempfile documentation](https://docs.python.org/3/library/tempfile.html)
- [Pygame documentation](https://www.pygame.org/docs/)
- [MiniLibX documentation (42 Docs)](https://harm-smits.github.io/42docs/libs/minilibx), for the MLX equivalence table
- [PyInstaller documentation](https://pyinstaller.org/en/stable/)
- [itch.io creator documentation](https://itch.io/docs/creators/getting-started)
- The assigned mazegenerator wheel's source and metadata document its actual API.

AI assistance:

- Dev A (core): roadmap planning, bug reviews, runtime verification,
  documentation, the terminal submission flow, and the A1–A10 regression tests.
  The original structure of the highscore manager was retained when applying fixes.
- Dev B (frontend): planning the frontend tasks, reviewing each task against
  the subject, writing the frontend unit and integration tests and the
  docstrings, checking the Linux package in a clean container, and writing the
  project-management records, the package's text files, and the frontend
  sections of this README. The frontend code, `pac-man.py`, and the packaging
  scripts were written by Dev B.
