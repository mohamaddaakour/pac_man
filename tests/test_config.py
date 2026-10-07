"""Unit tests for pacman configuration."""

from __future__ import annotations

from pathlib import Path

# import pytest

from pacman.config import Config, load_config


def write(tmp_path: Path, text: str) -> Path:
    """Write `text` into a tmp file and return its path."""

    path = tmp_path / "config.json"
    path.write_text(text, encoding="utf-8")

    return path


def load(tmp_path: Path, text: str) -> tuple[Config, list[str]]:
    messages: list[str] = []

    config = load_config(write(tmp_path, text), messages.append)

    return config, messages


def test_comments_ignored(tmp_path: Path) -> None:
    text = (
        "# full-line comment\n"
        "{\n"
        "    // C++ style comment\n"
        '    "lives": 5,\n'
        "      # indented comment\n"
        "      /* hello world what are you doing */"
        '    "points_per_ghost": 300\n'
        "}\n"
    )

    # Create Config instance
    config, _ = load(tmp_path, text)

    assert config.lives == 5
    assert config.points_per_ghost == 300
