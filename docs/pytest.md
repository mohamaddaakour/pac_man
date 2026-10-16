# Core test guide

Install `requirements.txt` into the active virtual environment, then run:

```bash
python -m pytest -q tests
python -m flake8 .
python -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

These are the checks behind `make test` and `make lint`. On Windows, use
`.venv\Scripts\python.exe` if the environment is not activated. If process
creation is restricted, `python -m flake8 . --jobs=1` uses the same lint rules
without worker subprocesses.

| Tasks | Tests | What they establish |
| --- | --- | --- |
| A1 | test_config.py | Comments, filename independence, defaults, clamps, types, diagnostics, parser/file errors |
| A2 | test_maze_adapter.py | Assigned API with perfect=False, mask conversion, 20 connected mazes, retry/failure handling, reproducible generation |
| A3 | test_entities.py | Direction vectors, boundaries, nearest center/corner spawns, invalid grids |
| A4–A8 | test_game_state.py | Buffered turns, elapsed time, scoring, collisions, grace, power, respawns, timeout, transitions, cheats |
| A6 | test_ghost_ai.py | BFS chase/flee behavior, 70% branch threshold, reversal constraints |
| A8 | test_levels.py, test_campaign.py | Ten-level expansion, random later levels, immutable config, real pellet-collecting campaign to victory |
| A9 | test_highscore.py | Validated top ten, stable ties, reload, corrupt input, atomic-write failures and cleanup |
| A10 | test_cli_demo.py | Menu, pause, wins/losses, name entry, cancellation/retry, relative storage, launch errors |

`tests/core_helpers.py` supplies deterministic rooms for focused behavior tests.
The campaign test uses the real assigned generator, real movement, and real
collection. Its BFS is only a test driver for player inputs, not a replacement
maze generator or game AI. Invisibility prevents random ghost damage while it
collects every pellet through ten levels; it does not call `skip_level()`.

Pytest provides `tmp_path`, a temporary `pathlib.Path`, to tests that declare it
as a parameter. Tests write score/config fixtures there, never to the player's
real score file. Permission and replacement failures are injected so they are
reliable on Windows and Unix. A real deployment-directory permission check
remains part of manual acceptance.

The existing window tests use SDL's dummy display driver through `conftest.py`.
Passing them does not replace keyboard, display, and packaged-build acceptance.
