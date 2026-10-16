"""A9: validation, ranking, persistence, and failed-write recovery."""

import json
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from pacman.highscore import Highscores


def test_missing_file_warns_and_starts_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """A first run can proceed without an existing score file."""
    scores = Highscores(str(tmp_path / 'scores.json'))
    scores.load()
    assert scores.top10() == []
    assert 'missing' in capsys.readouterr().err


@pytest.mark.parametrize('content', ['', '{bad', '{}', 'null'])
def test_empty_and_corrupt_storage_is_nonfatal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], content: str,
) -> None:
    """Malformed files produce a warning and an empty list."""
    path = tmp_path / 'scores.json'
    path.write_text(content, encoding='utf-8')
    scores = Highscores(str(path))
    scores.load()
    assert scores.top10() == []
    assert '[highscores]' in capsys.readouterr().err


def test_invalid_encoding_and_read_errors_are_nonfatal(
    tmp_path: Path,
) -> None:
    """Handle decode and permission errors inside the persistence API."""
    path = tmp_path / 'scores.json'
    path.write_bytes(b'\xff\xfe')
    scores = Highscores(str(path))
    scores.load()
    assert scores.top10() == []
    assert scores.last_error
    with patch.object(
        Path, 'read_text', side_effect=PermissionError('denied'),
    ):
        scores.load()
    assert scores.top10() == []
    assert scores.last_error and 'denied' in scores.last_error


def test_loaded_rows_are_validated_and_sorted(tmp_path: Path) -> None:
    """Only valid name-score pairs participate in ranking."""
    path = tmp_path / 'scores.json'
    path.write_text(json.dumps([
        ['Low', 0], ['High', 300], ['Tie', 300],
        ['!', 400], [' ', 500], ['ElevenChars', 1],
        ['Bool', True], ['Negative', -1], ['Float', 1.5],
        ['String', '5'], [10, 50], ['Missing'], None,
    ]), encoding='utf-8')
    scores = Highscores(str(path))
    scores.load()
    assert scores.top10() == [('High', 300), ('Tie', 300), ('Low', 0)]
    copy = scores.top10()
    copy.clear()
    assert len(scores.top10()) == 3


@pytest.mark.parametrize('name', ['', ' ', 'A!', 'ElevenChars', 'A\n', 'é'])
def test_invalid_names_do_not_create_files(tmp_path: Path, name: str) -> None:
    """Name validation precedes any write."""
    path = tmp_path / 'scores.json'
    scores = Highscores(str(path))
    assert not scores.add(name, 100)
    assert scores.last_error
    assert not path.exists()


@pytest.mark.parametrize('value', [-1, True, 1.5, '100', None])
def test_invalid_scores_are_rejected(tmp_path: Path, value: object) -> None:
    """Runtime callers cannot bypass non-negative integer validation."""
    scores = Highscores(str(tmp_path / 'scores.json'))
    score = cast(int, value)
    assert not scores.qualifies(score)
    assert not scores.add('Player', score)
    assert scores.top10() == []


def test_top_ten_save_reload_and_cutoff_ties(tmp_path: Path) -> None:
    """Eleven submissions retain ten; cutoff ties preserve earlier entries."""
    path = tmp_path / 'nested' / 'scores.json'
    scores = Highscores(str(path))
    for number in range(11):
        assert scores.add(f'Player{number}', number * 10)
    expected = [(f'Player{n}', n * 10) for n in range(10, 0, -1)]
    assert scores.top10() == expected
    before = path.read_bytes()
    assert not scores.qualifies(10)
    assert not scores.add('Equal', 10)
    assert path.read_bytes() == before
    reloaded = Highscores(str(path))
    reloaded.load()
    assert reloaded.top10() == expected


def test_valid_name_boundaries_and_zero_score(tmp_path: Path) -> None:
    """One/ten-character names and zero scores survive serialization."""
    scores = Highscores(str(tmp_path / 'scores.json'))
    assert scores.add('A', 0)
    assert scores.add('Ab 1234567', 1)
    scores.load()
    assert scores.top10() == [('Ab 1234567', 1), ('A', 0)]


@pytest.mark.parametrize('operation', [
    'tempfile.mkstemp', 'os.fsync', 'os.replace',
])
def test_failed_save_preserves_memory_disk_and_cleans_tempfiles(
    tmp_path: Path, operation: str,
) -> None:
    """Permission/flush/replace failures leave the original table intact."""
    path = tmp_path / 'scores.json'
    scores = Highscores(str(path))
    assert scores.add('Original', 100)
    original = path.read_bytes()
    with patch(
        f'pacman.highscore.{operation}', side_effect=PermissionError('denied'),
    ):
        assert not scores.add('New', 200)
    assert scores.top10() == [('Original', 100)]
    assert path.read_bytes() == original
    assert scores.last_error and 'denied' in scores.last_error
    assert list(tmp_path.glob('.highscores-*')) == []


def test_directory_used_as_score_file_is_nonfatal(tmp_path: Path) -> None:
    """An invalid destination produces an error instead of a traceback."""
    scores = Highscores(str(tmp_path))
    scores.load()
    assert scores.top10() == []
    assert not scores.add('Player', 100)
    assert scores.last_error
