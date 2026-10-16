# Developer A handoff — 2026-10-16

Scope: the A1–A11 core/persistence/test/documentation deliverables from the local
roadmap/jobs.md and roadmap/overview.md, checked against subject.md. Those source
planning files are locally ignored; this tracked handoff records the outcomes.

The implementation and checks are complete locally on feature/win-lose and
await partner review. No new commit, PR opening, merge, or publication is claimed.

## Deliverables

| Job | Implementation | Verification |
| --- | --- | --- |
| A1 Config | pacman/config.py | test_config.py |
| A2 Maze adapter | pacman/maze_adapter.py; assigned wheel unchanged | test_maze_adapter.py, including twenty connected real mazes |
| A3 Entities/spawns | pacman/entities.py | test_entities.py and generated-map spawn checks |
| A4 Movement | GameState buffered timed movement | test_game_state.py |
| A5 Pacgums | GameState placement, collection, power and scores | test_game_state.py, test_campaign.py |
| A6 Ghost AI | pacman/ghost_ai.py and per-ghost timers | test_ghost_ai.py, test_game_state.py |
| A7 Collisions/lives/invisibility | GameState collision and respawn rules | Same/shared/swapped-tile checks, grace, 100 protected contacts |
| A8 Timer/levels/results | pacman/levels.py and GameState | test_levels.py, test_game_state.py, real ten-level collection test |
| A9 Highscores | pacman/highscore.py | test_highscore.py, including simulated unwritable storage |
| A10 Tests/terminal demo | tools/cli_demo.py and tests | Win/loss, pause, cheats, names, scores, errors, menu return |
| A11 Core README/handoff | README.md, docs/core-api.md, docs/pytest.md | Reviewed against current behavior |
| Shared A-owned documents | acceptance.md and risks.md | Results and outstanding joint/frontend checks recorded |

## Contract for Developer B

- B3: `state.total_levels` is a read-only integer; render
  `f"LEVEL {state.level}/{state.total_levels}"`.
- B4/B5: `state.skip_level()` immediately completes an active level. It preserves
  score/lives, sets level_won on nonfinal levels and game_won on the final level,
  and does nothing outside playing. Suppress this key while paused/name editing.
- For level_won, show the transition then call `next_level()` and rebuild layout
  and cached walls. Catch MazeError and allow a clear failure/retry flow.
- After any win or loss, offer name entry. A validated nonqualifying score should
  receive an explanation and return to the menu without changing the top ten.
- Eaten ghosts respawn NORMAL even while an old edible_timer remains. Draw each
  ghost's state rather than treating every ghost as edible from the global timer.
- Later campaign levels are random; only level 1 uses a fixed seed.
- B7: the root launcher still runs the terminal application, but its extension
  restriction has been removed. Retain exactly-one-argument validation when
  replacing it with the graphical application.
- The four old main-branch lint findings are already fixed on this branch.
- The B2 render_demo belongs to the partner's branch; use it after combining
  the renderer and core changes. The older graphical_demo is separate and still
  lacks the skip key and unconditional name-entry flow.

## Proposed timeline updates for Developer B

Keep B's existing rows and confirmed merge dates when resolving timeline.md.
Its current vocabulary defines Done as merged and In review as an open PR, so
neither status should be inferred merely from this local implementation.

| Rows | Proposed update |
| --- | --- |
| A1–A7 | Retain confirmed merge history; add the new regression-test coverage |
| A8 | Locally implemented and verified: timer, >=10 levels, results, HUD count and skip; set In review when PR is open |
| A9 | Locally implemented and verified: validated atomic top ten; set In review when PR is open |
| A10 | Locally implemented and verified: terminal flows and A1–A9 tests; set In review when PR is open |
| A11 | Core README, API contract, risks and acceptance updated; review with B |
| B8 | Core APIs available; final renderer/app integration remains joint work |

The 174-test full-suite result and its environment are recorded in acceptance.md.
Packaging, publication, real-display acceptance and the cross-explanation session
remain delivery/team activities, not completed by these local changes.
