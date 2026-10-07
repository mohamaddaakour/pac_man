"""Unit tests for pacman configuration."""

from __future__ import annotations

from pathlib import Path

import json

import pytest

from pacman.config import (
    DEFAULT_LEVELS, Config, ConfigError, load_config, _strip_comments,
)


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


def test_strip_comments_keeps_line_numbers() -> None:
    assert _strip_comments("a\n#b\nc").splitlines() == ["a", "  ", "c"]


def test_unknown_key_is_ignored_with_message(tmp_path: Path) -> None:
    config, messages = load(tmp_path, '{"lives": 2, "banana": 1}')
    assert config.lives == 2
    assert not hasattr(config, "banana")
    assert "Unknown key `banana`, it will be ignored" in messages


def test_missing_key_uses_default_and_reports(tmp_path: Path) -> None:
    config, messages = load(tmp_path, '{}')
    assert config.lives == 3
    assert config.levels == DEFAULT_LEVELS
    assert any('`lives` is missing' in message for message in messages)


@pytest.mark.parametrize('value, expected', [(-1, 1), (100, 9), (10**400, 9)])
def test_lives_are_clamped(
    tmp_path: Path, value: int, expected: int,
) -> None:
    config, messages = load(tmp_path, json.dumps({'lives': value}))
    assert config.lives == expected
    assert any('minimum' in msg or 'maximum' in msg for msg in messages)


@pytest.mark.parametrize('value', ['3', True, None, 3.5])
def test_wrong_type_uses_default(tmp_path: Path, value: object) -> None:
    config, messages = load(tmp_path, json.dumps({'lives': value}))
    assert config.lives == 3
    assert any('`lives` must be an integer' in msg for msg in messages)


@pytest.mark.parametrize('value', [None, 42, {}, [], [None]])
def test_unusable_levels_use_defaults(tmp_path: Path, value: object) -> None:
    config, messages = load(tmp_path, json.dumps({'levels': value}))
    assert config.levels == DEFAULT_LEVELS
    assert any('`levels`' in msg for msg in messages)


def test_bom_is_accepted(tmp_path: Path) -> None:
    config, _ = load(tmp_path, '\ufeff{"lives": 5}')
    assert config.lives == 5


def test_comments_preserve_strings_and_multiline_positions() -> None:
    text = (
        '{/* first\nsecond */ "url": "https://example.com", '
        '"text": "escaped \\" // /* #"} // trailing'
    )
    stripped = _strip_comments(text)
    assert json.loads(stripped) == {
        'url': 'https://example.com', 'text': 'escaped " // /* #',
    }
    assert len(stripped) == len(text)
    assert stripped.index('\n') == text.index('\n')


@pytest.mark.parametrize('text', ['{"lives":}', '[]', '{ /* unclosed'])
def test_invalid_files_raise_config_error(tmp_path: Path, text: str) -> None:
    with pytest.raises(ConfigError):
        load(tmp_path, text)


def test_missing_file_raises_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match='not found'):
        load_config(tmp_path / 'missing.json')


def test_parser_integer_limit_raises_config_error(tmp_path: Path) -> None:
    import sys

    get_limit = getattr(sys, 'get_int_max_str_digits', None)
    if get_limit is None or get_limit() == 0:
        pytest.skip('Interpreter does not enforce an integer digit limit')
    text = '{"lives": ' + '9' * (get_limit() + 1) + '}'
    with pytest.raises(ConfigError, match='parser limits'):
        load(tmp_path, text)
