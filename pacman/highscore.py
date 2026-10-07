from __future__ import annotations


class HighScores:
    """Top-10 highscores stored on disk."""

    def __init__(self, file_name: str) -> None:
        """Where the list lives"""
        self.file_name = file_name

    def load(self) -> None:
        raise NotImplementedError

    def qualifies(self, score: int) -> bool:
        """True if `score` would enter the top 10."""
        raise NotImplementedError

    def add(self, name: str, score: int) -> bool:
        raise NotImplementedError

    def top10(self) -> list[tuple[str, int]]:
        raise NotImplementedError
