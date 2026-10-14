"""Shared score loading and presentation for the runnable applications."""

from __future__ import annotations

from pathlib import Path

from pacman.config import Config
from pacman.highscore import Highscores


def load_highscores(config: Config, config_path: str) -> Highscores:
    """Resolve relative storage beside the config, independently of cwd."""
    path = Path(config.highscore_filename)
    if not path.is_absolute():
        path = Path(config_path).resolve().parent / path
    scores = Highscores(str(path))
    scores.load()
    return scores


def score_lines(scores: Highscores) -> list[str]:
    """Format a compact ranked table shared by terminal and window menus."""
    entries = scores.top10()
    if not entries:
        return ['No scores yet.']
    return [f'{rank:2}. {name:<10} {score}'
            for rank, (name, score) in enumerate(entries, start=1)]
