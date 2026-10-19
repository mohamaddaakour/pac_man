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
| A8. Timer, levels, win/lose | Dev A | TBD | 2026-10-12 | | In progress | `level_won` and `game_over` set; timer and `next_level()` pending |
| A9. Highscores | Dev A | TBD | | | Not started | |
| A10. Tests and CLI demo | Dev A | TBD | | | Not started | |
| A11. README (core sections) | Dev A | TBD | | | Not started | |
| Frontend file skeleton | Dev B | TBD | 2026-10-08 | 2026-10-08 | Done | |
| B1. pygame window wrapper | Dev B | TBD | 2026-10-08 | 2026-10-12 | Done | 16 unit tests, `tools/window_demo.py` |
| B2. Sprites and tile rendering | Dev B | TBD | 2026-10-13 | | In review | 45 unit tests, `tools/render_demo.py` |
| B3. HUD | Dev B | TBD | | | Not started | |
| B4. Input | Dev B | TBD | | | Not started | |
| B5. App state machine | Dev B | TBD | | | Not started | |
| B6. Screens | Dev B | TBD | | | Not started | |
| B7. Entry point | Dev B | TBD | | | Not started | |
| B8. Integration with the core | Dev A + Dev B | TBD | | | Not started | The core it needs (A3–A7) is merged |
| B9. Packaging and itch.io | Dev B | TBD | | | Not started | |
| B10. Tests and README (frontend sections) | Dev B | TBD | | | Not started | |
| Project management documents | Dev A + Dev B | TBD | 2026-10-08 | | In progress | |


## Core implementation update — 2026-10-14

Persistence, application menu/name entry, root entry-point validation, runtime
hardening, core API handoff, and acceptance/risk documentation are implemented
in the working tree. Runtime acceptance and lint passed; no merge/PR completion
is claimed here. Unit tests were excluded by explicit request. Frontend packaging
and real-display acceptance remain separate tasks.
