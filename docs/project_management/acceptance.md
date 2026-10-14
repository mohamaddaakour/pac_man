# Core acceptance record

Verified on 2026-10-14 with runtime scripts and headless graphical checks.
No unit tests were added or run for this completion. Existing test files remain
unchanged. This is a runtime acceptance record, not a claim of full unit coverage.

| Check | Result |
|---|---|
| Highscores save and reload | Passed; JSON pairs preserve descending order |
| Eleven submissions | Passed; table contains the best ten |
| Full-table cutoff ties | Passed; new tied scores do not displace old entries |
| Invalid name, spaces-only, long name, boolean score | Passed; submission rejected |
| Invalid encoding and corrupt JSON | Passed; warning and empty fallback |
| Mixed valid/invalid stored rows | Passed; only valid pairs loaded |
| Defensive top10 copy | Passed; caller changes do not affect stored entries |
| Read-only score directory | Passed; False result, error message, unchanged table |
| Temporary-file cleanup after failure | Passed; no leftover temporary file |
| Graphical menu and highscore table | Passed with SDL dummy driver |
| Timeout -> game over -> name entry | Passed using actual countdown/core update |
| Graphical name cap, Backspace, and Enter | Passed; accepted name saved once |
| Restart, abandoned game, return to menu, quit | Passed; no score for abandonment |
| Terminal menu -> game over -> name -> table -> menu | Passed with scripted stdin |
| Launch from another directory | Passed; scores stored beside the config |
| Missing/extra config arguments and missing file | Passed; failure code, no traceback |
| make lint and make lint-strict | Passed for 35 source files |

Earlier runtime review played through ten generated levels with invisibility and
a 600-second timer, verified pause, carry-over score/lives, timeout, game_won, and
layout rebuilding. This completion preserves those core rules; its new runtime
checks focus on persistence, application flow, and entry-point errors.

## Remaining acceptance work

- Run on a real display with keyboard and window close controls.
- Complete the teammate's renderer/screens/app integration against docs/core-api.md.
- Tune the default timer and difficulty with human playthroughs.
- Add/run unit coverage separately if requested; it was explicitly excluded here.
- Package and publish a final graphical build as a separate delivery task.

## Manual checklist for the next handoff

1. Launch either application, open instructions and the score table, and return.
2. Start a campaign; move, pause/resume, use invisibility, and clear a level.
3. Advance with N; verify timer reset and changed maze walls/layout.
4. Reach win or loss; enter an invalid name, correct it, and save a valid one.
5. Restart the application; confirm the saved score and rank survive.
6. Try an unwritable score directory; verify retry/skip rather than a crash.
7. Cancel an unfinished game; confirm the table is unchanged.
