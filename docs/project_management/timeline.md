# Timeline

Planned vs actual progress for every task. Dates come from the Git history.
Update the row of a task when it starts, when its pull request is opened, and when it is merged.

Status: Not started, In progress, In review (pull request open), Done (merged into `main`).

| Task | Owner | Planned end | Started | Finished | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 0. Project setup (repo, Makefile, conventions, stubs) | Dev A + Dev B | TBD | 2026-10-04 | 2026-10-04 | Done | |
| A1. Config loader | Dev A | TBD | 2026-10-04 | 2026-10-07 | Done | 23 unit tests |
| A2. Maze adapter | Dev A | TBD | 2026-10-07 | 2026-10-12 | Done | |
| A3. Entities and grid helpers | Dev A | TBD | 2026-10-04 | 2026-10-12 | Done | Spawn rules in `choose_spawns` |
| A4. Player movement | Dev A | TBD | 2026-10-12 | 2026-10-12 | Done | |
| A5. Pacgums | Dev A | TBD | 2026-10-12 | 2026-10-12 | Done | Merged with A4 |
| A6. Ghost AI | Dev A | TBD | 2026-10-12 | 2026-10-13 | Done | |
| A7. Collisions, lives, invisibility | Dev A | TBD | 2026-10-12 | 2026-10-12 | Done | |
| A8. Timer, levels, win/lose | Dev A | TBD | 2026-10-12 | 2026-10-16 | Done | At least 10 levels, `total_levels`, `skip_level()` cheat |
| A9. Highscores | Dev A | TBD | 2026-10-14 | 2026-10-16 | Done | Validated top 10, atomic save |
| A10. Tests and CLI demo | Dev A | TBD | 2026-10-14 | 2026-10-16 | Done | Terminal demo; core tests (219 in the full suite) |
| A11. README (core sections) | Dev A | TBD | 2026-10-14 | 2026-10-16 | Done | Plus `docs/core-api.md` and the handoff |
| Frontend file skeleton | Dev B | TBD | 2026-10-08 | 2026-10-08 | Done | |
| B1. pygame window wrapper | Dev B | TBD | 2026-10-08 | 2026-10-12 | Done | 16 unit tests, `tools/window_demo.py` |
| B2. Sprites and tile rendering | Dev B | TBD | 2026-10-13 | 2026-10-19 | Done | 45 unit tests, `tools/render_demo.py` |
| B3. HUD | Dev B | TBD | 2026-10-20 | | In review | 12 unit tests; branch `feature/graphical-app` |
| B4. Input | Dev B | TBD | 2026-10-20 | | In review | 40 unit tests; branch `feature/graphical-app` |
| B5. App state machine | Dev B | TBD | 2026-10-21 | | In review | 26 unit tests; branch `feature/graphical-app` |
| B6. Screens | Dev B | TBD | 2026-10-22 | | In review | 18 unit tests; branch `feature/graphical-app` |
| B7. Entry point | Dev B | TBD | 2026-10-23 | | In review | 15 unit tests; `make run` launches the graphical game |
| B8. Integration with the core | Dev A + Dev B | TBD | 2026-10-29 | | In progress | Real-display acceptance pass; branch `feature/graphical-app` |
| B9. Packaging and itch.io | Dev B | TBD | | | Not started | |
| B10. Tests and README (frontend sections) | Dev B | TBD | | | Not started | |
| Project management documents | Dev A + Dev B | TBD | 2026-10-08 | | In progress | |


## Core implementation update — 2026-10-14

Persistence, application menu/name entry, root entry-point validation, runtime
hardening, core API handoff, and acceptance/risk documentation are implemented
in the working tree. Runtime acceptance and lint passed; no merge/PR completion
is claimed here. Unit tests were excluded by explicit request. Frontend packaging
and real-display acceptance remain separate tasks.
