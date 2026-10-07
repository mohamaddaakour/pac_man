"""Unit tests for pacman configuration."""

from __future__ import annotations

from pathlib import Path

# import pytest

from pacman.config import Config, load_config, _strip_comments


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
        "    # indented comment\n"
        "    /* hello world what are you doing */\n"
        '    "points_per_ghost": 300,\n'
        '    "points_per_ghots": 200,\n'
        '    "points_per_ghost": 250\n'
        "}\n"
    )

    # Create Config instance
    config, _ = load(tmp_path, text)

    # print(f"\n\nConfiguration: {config}")

    assert config.lives == 5
    assert config.points_per_ghost == 250


def test_stip_comments_keeps_line_numbers() -> None:
    assert _strip_comments("a\n#b\nc").split() == ["a", "c"]


def test_unknown_key_is_ignored_with_message(tmp_path: Path) -> None:
    config, messages = load(tmp_path, '{"lives": 2, "banana": 1}')
    assert config.lives == 2
    assert not hasattr(config, "banana")
    assert "Unknown key `banana`, it will be ignored" in messages