# Team organization

## Roles

| Developer | Login | Scope |
| --- | --- | --- |
| Dev A | mdaakour | Game core and persistence: config, maze adapter, entities, movement, ghost AI, game state, highscores, CLI demo |
| Dev B | gmoujaes | Frontend and delivery: graphics wrapper, rendering, HUD, input, screens, app state machine, entry point, packaging, itch.io |

## Workflow

- One branch per feature (`feature/<name>`), merged into `main` through a pull request reviewed by the other developer.
- `make lint` and `make test` must pass before a pull request is opened.
- Shared files (Makefile, `requirements.txt`, `.gitignore`, README) are changed only after telling the other developer.

## Decision log

| Date | Decision | Reason | Owner |
| --- | --- | --- | --- |
| 2026-10-04 | Shared conventions: positions are `(row, col)`, grid tiles are 0 (corridor) or 1 (wall), time is in seconds (float) | Both halves use the same units and coordinates | Dev A + Dev B |
| 2026-10-04 | The core (`pacman/`) never depends on graphics | The core can be tested and played in a terminal | Dev A + Dev B |
| 2026-10-07 | Graphics library: pygame, using only functions that have an MLX equivalent; pygame is imported only in `frontend/window.py` | Subject IV allows a library "similar to MLX". Compared with MLX42 (C library used through ctypes): no native build, normal Python exceptions instead of crashes, type hints for mypy, and PyInstaller bundles it without extra work | Dev B |
| 2026-10-08 | Frontend lives in its own package, `frontend/` | Keeps the graphics separate from the core | Dev B |
| 2026-10-08 | `tests/` is a package (`tests/__init__.py`) | Tests share helpers from `tests/fakes.py`, and mypy needs the package to resolve them | Dev B |
| 2026-10-13 | The renderer reads the game through `GameStateProtocol`; mypy checks the real `GameState` against it | Frontend and core can be built in parallel, and any mismatch is a lint error | Dev B |
| 2026-10-14 | The highscore file is stored next to the config file | Scores do not depend on the folder the game is launched from | Dev A |
| 2026-10-16 | Cheats: I toggles invisibility, K skips a level | Lets a reviewer reach every level and screen quickly (subject VI.5) | Dev A + Dev B |
| 2026-10-30 | The name prompt is shown after every game; a score outside the top 10 is not saved | The subject's game over and victory screens always prompt for a name | Dev A + Dev B |
| 2026-10-30 | The maze's 42 pattern is drawn in its own colour; ghosts always have eyes; the HUD sits right above the maze | Makes the generator's 42 visible and keeps the HUD aligned for every maze shape | Dev B |

## Open questions

- Location of the highscore file in the packaged game (task B9).

The other questions were settled during integration (see the decision log).

## Blocking points

| Date | Problem | Resolution |
| --- | --- | --- |
| 2026-10-07 | MLX42's Python binding is incomplete (no key hook, close hook or text function) | Switched to pygame (see decision log) |
| 2026-10-29 | 99×99 mazes stutter: the ghosts' BFS (`distance_map`) takes about 49 ms each time Pac-Man enters a tile, over the 16.7 ms frame | Numbers sent to Dev A; a BFS that reads the direction offsets once takes 12 ms (open) |
