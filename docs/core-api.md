# Core API contract

Positions are (row, col) integers. Grid values are 0 corridor / 1 wall. Time is
seconds. Generated tile dimensions are 2× configured cell dimensions + 1.

## Startup and ownership

load_config(path) returns Config or raises ConfigError. GameState(config) plans
at least ten levels and generates the first maze, raising MazeError if needed.
The core owns scores, lives, pellets, positions, timers, and ghost decisions.
The UI owns menu/pause/name-entry state and catches startup/transition failures.

## GameState

| Member | Contract |
|---|---|
| grid | Rectangular list of integer tile rows |
| player | Entity with pos and direction |
| ghosts | Four Ghost objects; pos, direction, state, respawn_timer, movement_elapsed |
| pacgums / super_pacgums | Sets of remaining tile positions |
| score / lives / level | Score, remaining lives, one-based level number |
| levels | Expanded immutable level plan; its length is the campaign length |
| time_left / edible_timer / grace_timer | Remaining seconds |
| invisible | Normal-ghost damage protection, not timeout protection |
| status | playing, level_won, game_won, or game_over |
| set_direction(Direction) | Queue a buffered turn; no immediate movement |
| toggle_invisibility() | Flip the cheat flag |
| update(dt) | Advance finite non-negative seconds only during playing |
| next_level() | Advance only level_won; preserves score/lives/cheat |

Calling next_level in another status raises ValueError. Failed generation leaves
the previous state intact. After a successful transition, rebuild every
maze-dependent background/layout cache even when dimensions have not changed.
Pause by omitting update, not by changing core status. Terminal statuses freeze
movement and timers. GameState does not save scores or ask for a player name.

GhostState.NORMAL chases and damages; EDIBLE flees and scores when eaten;
EATEN is hidden/inactive until its countdown completes. Do not alter movement or
respawn accumulators from the renderer. The UI uses Direction, not raw vectors.

## Persistence

Highscores(file_name) stores the path without performing I/O. load() populates
an empty or valid top-ten table, reporting unreadable/corrupt files as warnings.
qualifies(score) rejects booleans/negative/non-integer scores and requires a score
above the last entry when full. add(name, score) validates and saves; True means
the score was persisted, False means validation/qualification/save failed.
last_error provides a readable submission error. top10() returns a defensive copy.

Names contain 1–10 ASCII letters/digits/spaces with at least one non-space.
Storage is a JSON list of [name, score] pairs. Existing tied scores retain order.
load_highscores(config, config_path) in tools/session.py resolves relative paths
beside the config file. Call it at startup and share the returned manager.

At game_won/game_over, offer one name submission if eligible, then return to the
menu. Cancelled games submit nothing. Keep failed save attempts retryable without
changing the table. Ignore game hotkeys while editing a name, including Q/I/P.
A new campaign requires a new GameState; preserve the shared Highscores manager.

## Error boundaries

Catch ConfigError and MazeError at startup and transitions. Graphical failures
must release the Window context and return a nonzero exit code. Persistence
errors stay nonfatal and must be shown to the user. Keep final exception handling
at the application boundary rather than masking core failures during a frame.

## Scope

The terminal and standalone graphical applications implement the core flow.
The teammate's renderer/app/screens remain separate frontend work. Packaging,
external publishing, and final graphical acceptance are outside this core handoff.
Unit tests were neither added nor run for this completion; use the acceptance
checklist for the recorded runtime checks.
