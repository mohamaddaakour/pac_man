"""Persistent top-10 highscore manager."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Iterable

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

    def load(self) -> None:
        """Load and validate entries."""
        self._entries = []

        # If the file doesn't exist ther is nothing to load
        if not self._path.exists():
            return
        
        try:
            # Read the highscore's file content
            raw = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            _warn(f"Could not read highscores: {exc}")
            return
        
        if not raw.strip():
            _warn(f"Highscore file is empty, starting fresh now.")
            return
        
        try:
            # Parsing the JSON file: Convert the data inside the
            # highscore file from JSON format to a Python data structure
            data = json.load(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            _warn(f"Higscore file is corrupted ({exc}), starting fresh now.")
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

            if not isinstance(name, str) or NAME_PATTERN.fullmatch(name) is None:
                continue

            if isinstance(score, bool) or not isinstance(score, int):
                continue

            if score < 0:
                continue

            parsed.append((name, int(score)))

        # Sort from the highscore to the lowest score
        parsed.sort(key=lambda pair: pair[score], reverse=True)

        # Get top 10 players
        self._entries = parsed[:10]
    
    def _validate_name(self, name: str) -> bool:
        return isinstance(name, str) and NAME_PATTERN.fullmatch(name) is not None

    def _validate_score(self, score: int) -> bool:
        return (isinstance(score, int) and not isinstance(score, bool)
                and score >= 0)

    def qualifies(self, score: int) -> bool:
        """True if `score` would enter the top 10."""
        if not self._validate_score(score):
            return False
        if len(self._entries) < 10:
            return True
        return score >= self._entries[-1][1]

    def add(self, name: str, score: int) -> bool:
        raise NotImplementedError

    def top10(self) -> list[tuple[str, int]]:
        """Return a defensive copy of the sorted list."""
        return list(self._entries)
