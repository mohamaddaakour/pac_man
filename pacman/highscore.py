"""Persistent top-10 highscore manager."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

# The player name should be a string from 1 to 10 characters
# and contain upper or lower case characters and numbers
NAME_PATTERN = re.compile(r"^[A-Za-z0-9 ]{1,10}$")


def _warn(message: str) -> None:
    """Print a warning message."""
    print(f"[highscores] {message}", file=sys.stderr)


class Highscores:
    """Top-10 highscores stored on disk.

    Names: 1-10 characters of letters, digits, or spaces.
    Scores: non-negative integers. Capacity: 10, descending.
    """

    def __init__(self, file_name: str) -> None:
        """Where the list lives"""
        self.file_name = file_name
        self._path = Path(file_name)
        self._entries: list[tuple[str, int]] = []
        self.last_error: str | None = None

    def load(self) -> None:
        """Load and validate entries."""
        self._entries = []
        self.last_error = None

        try:
            # If the file doesn't exist there is nothing to load.
            if not self._path.exists():
                return
            # Read the highscore's file content
            raw = self._path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError, ValueError) as exc:
            self.last_error = f"Could not read highscores: {exc}"
            _warn(self.last_error)
            return

        if not raw.strip():
            _warn("Highscore file is empty, starting fresh now.")
            return

        try:
            # Parsing the JSON file: Convert the data inside the
            # highscore file from JSON format to a Python data structure
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError, RecursionError) as exc:
            _warn(f"Highscore file is corrupted ({exc}), starting fresh now.")
            return

        if not isinstance(data, list):
            _warn("Highscore must contain a list, starting fresh now.")
            return

        parsed: list[tuple[str, int]] = []

        for item in data:
            # `isinstance(item, (list, tuple))` check if the value of `item`
            # isn't list or tuple
            # item should contain the name of the player with its score
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue

            name, score = item

            if not isinstance(name, str) or not self._validate_name(name):
                continue

            if isinstance(score, bool) or not isinstance(score, int):
                continue

            if score < 0:
                continue

            parsed.append((name, int(score)))

        # Sort from the highscore to the lowest score
        parsed.sort(key=lambda pair: pair[1], reverse=True)

        # Get top 10 players
        self._entries = parsed[:10]

    def _validate_name(self, name: str) -> bool:
        """Accept the allowed characters and reject names of only spaces."""
        return (isinstance(name, str) and bool(name.strip())
                and NAME_PATTERN.fullmatch(name) is not None)

    def _validate_score(self, score: int) -> bool:
        """Accept non-negative integer scores, excluding booleans."""
        return (isinstance(score, int) and not isinstance(score, bool)
                and score >= 0)

    def qualifies(self, score: int) -> bool:
        """True if `score` would enter the top 10."""
        if not self._validate_score(score):
            return False
        if len(self._entries) < 10:
            return True
        return score > self._entries[-1][1]

    def add(self, name: str, score: int) -> bool:
        """Add a qualifying entry; return True only when it is saved."""
        self.last_error = None
        if not self._validate_name(name) or not self._validate_score(score):
            self.last_error = 'Use a valid name and a non-negative score'
            return False

        if not self.qualifies(score):
            self.last_error = 'This score does not enter the top ten'
            return False

        # Keep the old list so a failed save does not change memory either.
        previous = list(self._entries)
        self._entries.append((name, score))
        self._entries.sort(key=lambda pair: pair[1], reverse=True)
        self._entries = self._entries[:10]
        if not self._save():
            self._entries = previous
            return False

        return True

    def top10(self) -> list[tuple[str, int]]:
        """Return a defensive copy of the sorted list."""
        return list(self._entries)

    def _save(self) -> bool:
        """Write to a temporary file and atomically replace the score file."""
        try:
            # Create the directory of the highscore file with its parents.
            self._path.parent.mkdir(parents=True, exist_ok=True)

            # Create a temporary file beside the actual highscore file.
            fd, tmp_name = tempfile.mkstemp(
                dir=str(self._path.parent), prefix=".highscores-",
            )
            try:
                # Open the temporary file and write the list as JSON.
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(self._entries, handle)
                    # Send buffered data to the operating system.
                    handle.flush()
                    # Synchronize the file before replacing the old one.
                    os.fsync(handle.fileno())
                os.replace(tmp_name, self._path)
            finally:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
        except (OSError, ValueError, RecursionError) as exc:
            self.last_error = f"Could not save highscores: {exc}"
            _warn(self.last_error)
            return False

        return True
