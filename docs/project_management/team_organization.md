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

## Open questions (to agree before integration)

- Which `GameState` attributes the renderer reads (grid, player, ghosts, pacgums, timers, total levels, status).
- Extra cheats for reviewers (level skip, extra life) in addition to invisibility.
- Name entry: always prompt at the end of a game, and use the same name rules on screen and in the highscore file.
- Location of the highscore file when the packaged game is launched from another folder.

## Blocking points

| Date | Problem | Resolution |
| --- | --- | --- |
| 2026-10-07 | MLX42's Python binding is incomplete (no key hook, close hook or text function) | Switched to pygame (see decision log) |
