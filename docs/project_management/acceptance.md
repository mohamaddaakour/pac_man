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
