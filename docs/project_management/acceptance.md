# Core acceptance record

## Developer A verification — 2026-10-16

The full checked-out suite passed: **174 tests**, including the existing window
tests. Developer A's implementation and automated verification are ready for
partner review; this records local work, not a PR merge or final delivery.

| Check | Evidence / result |
| --- | --- |
| Config comments, defaults, clamps, unknown keys, invalid files | test_config.py; passed |
| Arbitrary config filename | Loader and root-launcher tests; settings.txt accepted |
| Assigned generator, perfect=False, conversion and retries | test_maze_adapter.py; passed without changing the package |
| Twenty connected generated grids and walkable distinct spawns | Twenty parametrized real-generator cases; passed |
| Movement, buffering, scoring, timing, collisions and grace | test_game_state.py; passed |
| Invisibility against 100 normal-ghost contacts | Passed; no life lost while enabled |
| Ghost chase/flee, random branch, no unnecessary reversal | test_ghost_ai.py; passed |
| Eaten ghost returns NORMAL after delay | Passed, including while the old power timer remains |
| Ten-level expansion and random later levels | test_levels.py; passed; input Config preserved |
| Ten-level victory by collecting all pellets | test_campaign.py; actual generated grids and update(), no skip calls |
| Skip cheat, HUD count, final victory and inactive-state behavior | test_game_state.py; passed |
| Timeout, game over, score/life carry-over, failed transition | test_game_state.py; passed |
| Highscore validation, eleven entries, stable ties, reload | test_highscore.py; passed |
| Read, temporary-file, flush and atomic-replacement failures | Injected PermissionError; table/file preserved and temporary files cleaned |
| Terminal win/loss to name entry to menu | test_cli_demo.py; passed |
| Nonqualifying name entry, cancellation and failed-save retry | test_cli_demo.py; passed |
| Pause suppresses movement and cheats | test_cli_demo.py; passed |
| Missing/extra arguments, missing/bad config, failed generator | Readable errors with no traceback; passed |
| Launch from another working directory | Scores resolve beside config; passed |
| Existing pygame window tests | Passed with SDL dummy driver; no real-display claim |
| Flake8 | Passed with --jobs=1 and the repository's configured rules |
| Required mypy checks | Passed; no issues in 43 source files |

### Environment and commands

Windows, Python 3.12.4. The project virtual environment contains the assigned
maze package and test tools. It lacked pygame, so this verification appended
the installed system Python site-packages directory to the test process's
search path. No dependency or frontend source was changed. A normally installed
environment should use `python -m pip install -r requirements.txt` first.

Pytest's private temporary-directory permissions were incompatible with the
restricted runner. The successful run used an unrestricted test process and
a fresh directory under the project's ignored `.pytest_cache`:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.append(r'C:\Users\user\AppData\Local\Programs\Python\Python312\Lib\site-packages'); import pytest; raise SystemExit(pytest.main(['-q', 'tests', '--basetemp=.pytest_cache/dev-a-verified-1', '-p', 'no:cacheprovider', '--tb=short']))"
```

Flake8 is checked with `--jobs=1` to avoid restricted worker-process creation.
Mypy uses all mandatory flags from the Makefile. GNU Make is unavailable in this
Windows shell, so the underlying lint/test commands are run directly; this is
not a claim that `make` itself was executed.

## Earlier record

The 2026-10-14 handoff recorded runtime persistence, terminal, and headless
graphical-demo checks, with no new unit tests at that time. This verification
adds automated coverage and supersedes that earlier testing limitation. It does
not independently re-certify every old graphical-demo scenario.

## Remaining shared / frontend acceptance

1. Dev B integrates the real core and score API; use total_levels and skip_level.
2. Show name entry after every win/loss, including nonqualifying scores.
3. Exercise menus, pause, level transitions, cheats, names and errors on a real
   display with the final graphical launcher.
4. Check an actually unwritable score directory in the target deployment.
5. Tune maze sizes/timers with human playthroughs; default 90 seconds can be tight.
6. Build/install on a clean machine, include controls/config instructions, and
   publish the final package. These remain Dev B's delivery and joint acceptance.
7. Review the PR together and explain each other's modules before the defense.

## Graphical acceptance — Dev B, 2026-10-30

The graphical game (`python3 pac-man.py <config>`) was played on a real
display against the subject (V.1, V.5 and chapter VI), with the ready-made
configs in `configs/`. Every check passed.

| Check | Config | Result |
| --- | --- | --- |
| Menu: four items, arrows or W/S, Enter, Esc; instructions show the config values | `config.json` | Passed |
| Level 1 is the same maze on every launch (seed 42); level 2 changes | `config.json` | Passed |
| Super-pacgums and ghosts start in the four corners, Pac-Man in the middle | `config.json` | Passed |
| Arrows and WASD; walls block; a turn pressed early is taken at the next junction | `configs/scoring.json` | Passed |
| Pacgum +1, super-pacgum +10, ghost +100; the score never goes down | `configs/scoring.json` | Passed |
| Ghosts chase, then flee and blink when edible; an eaten ghost goes back to its corner as eyes and is normal again after 5 s | `configs/scoring.json` | Passed |
| Ghost contact: one life lost, Pac-Man back in the middle | `config.json` | Passed |
| Timeout: one life lost and the timer restarts; time turns red under 10 s; game over screen | `configs/timeout.json` | Passed |
| "LEVEL n/10" transition; score and lives carried over; victory screen after level 10 | `config.json` | Passed |
| Cheats: K skips a level, I toggles invisibility | `config.json` | Passed |
| P or Esc pauses (timer and ghosts frozen); Resume and Main menu | `config.json` | Passed |
| Name rules, error on a bad name; saved name in the menu and the table, still there after a relaunch | `config.json` | Passed |
| Corrupt score file (`{`): the game starts with an empty table, no crash | `configs/` | Passed |
| Unwritable score folder (`chmod a-w configs`): the save error is shown and Esc leaves | `configs/` | Passed |
| Close button exits with code 0, Ctrl+C with 130 | any | Passed |
| Key spam during level transitions and on the end screen | any | Passed |
| 99×99 mazes | `configs/large.json` | Playable, but stutters (see Performance) |

### Automated checks

`tests/test_integration.py` drives the graphical app headless with the real
`GameState` and `Highscores` (9 tests): the ten-level campaign with K, the
larger maze drawn after a level change, pause freezing the real timer, a
game-over name saved and read back from disk, a full table that still asks
for a name but leaves the file unchanged, and 5×5, 99×5, 5×99 and 99×99
mazes. Full suite: **349 passed**; flake8 and both mypy configurations clean.

### Performance (headless, Linux, Python 3.11)

| Maze | Level build | Frame drawing (mean) | Core `update` (mean / worst) |
| --- | --- | --- | --- |
| 21×21 | 14 ms | 0.5 ms | 0.2 / 2 ms |
| 51×51 | 27 ms | 0.7 ms | 1.1 / 14 ms |
| 99×99 | 58 ms | 1.4 ms | 4.1 / 50 ms |

A frame at 60 FPS has 16.7 ms. At 99×99 the worst case comes back every time
Pac-Man enters a new tile: `ghost_ai.distance_map` takes about 49 ms. A
version that reads the direction offsets once returns identical distances in
12 ms. Reported to Dev A, who owns the fix.

### Decisions made during integration

- The name prompt is shown after every game, as the subject's game over and
  victory screens require. A score outside the top 10 is not saved: Enter
  returns to the menu with "Not in the top 10: score not saved".
- The maze's 42 pattern (fully closed cells) is drawn in green, ghosts keep
  their eyes in every state, and the HUD sits right above the maze.

### Remaining items from the list above

Items 1–3 are covered by this record. Item 4 was checked from source
(`chmod a-w configs`) and is checked again in the package during B9. Item 5:
the default 90 s timer was kept, and `configs/` provides longer timers for
review. Item 6 (packaging and itch.io) is task B9. Item 7 (joint review of
each other's modules) is planned before the defense.
