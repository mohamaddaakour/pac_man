# Core risks and decisions

| Risk | Handling / remaining work |
|---|---|
| Assigned generator changes or fails | Isolated adapter, mask/connectivity validation, capped retries, MazeError |
| Large mazes cannot fit a short timer | Configurable limit; use 300+ seconds for campaign verification |
| Unwritable/corrupt score storage | Empty fallback, validation, atomic replacement, retryable error |
| Concurrent applications overwrite scores | Single-process manager; locking is not implemented |
| Coordinate or state mismatch at frontend handoff | docs/core-api.md; total_levels and skip_level available; rebuild caches after every transition |
| Unfinished graphical frontend | Standalone graphical application uses only the existing window wrapper |
| Core regression | A1–A10 behavioral tests and a real ten-level campaign pass; see acceptance.md for scope |
| Dependency availability | requirements.txt pins the assigned wheel path; virtual environment and make install |
| Limited review time | K skips a terminal level without points; Dev B can bind skip_level() in the UI |
| Inconsistent name-entry flow | Terminal prompts after every completed game; final UI must also prompt for nonqualifying scores |
| Conflicting timeline edits | Preserve both branches' row updates; proposed A statuses are in dev-a-handoff.md |

The core uses JSON for inspectable persistence without a database. Score files
are relative to the configuration directory rather than the launch directory.
Cheat-assisted games are eligible for scores. Cancellation does not submit a score.
Later campaign levels always use random seeds, even if their config entries
specify seeds, to follow the subject. The first level remains deterministic.
Eaten ghosts respawn as NORMAL as specified in jobs.md, so a remaining old power
timer does not make a newly respawned ghost safe; the UI should draw its actual state.
