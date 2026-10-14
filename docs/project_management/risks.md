# Core risks and decisions

| Risk | Handling / remaining work |
|---|---|
| Assigned generator changes or fails | Isolated adapter, mask/connectivity validation, capped retries, MazeError |
| Large mazes cannot fit a short timer | Configurable limit; use 300+ seconds for campaign verification |
| Unwritable/corrupt score storage | Empty fallback, validation, atomic replacement, retryable error |
| Concurrent applications overwrite scores | Single-process manager; locking is not implemented |
| Coordinate or state mismatch at frontend handoff | docs/core-api.md; rebuild caches after every transition |
| Unfinished graphical frontend | Standalone graphical application uses only the existing window wrapper |
| Unit coverage incomplete | No new unit tests or unit-test execution by user request; runtime checks recorded |
| Dependency availability | requirements.txt pins the assigned wheel path; virtual environment and make install |

The core uses JSON for inspectable persistence without a database. Score files
are relative to the configuration directory rather than the launch directory.
Cheat-assisted games are eligible for scores. Cancellation does not submit a score.
