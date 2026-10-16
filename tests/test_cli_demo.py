"""A10: real terminal campaign flows and friendly startup errors."""

import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from pacman.game_state import GameState
from pacman.highscore import Highscores
from pacman.maze_adapter import MazeError
from tools import cli_demo
from tools.session import load_highscores
from tests.core_helpers import make_config, open_grid

ROOT = Path(__file__).resolve().parents[1]


def config_file(tmp_path: Path) -> Path:
    """Write a small campaign whose score file stays in the test directory."""
    path = tmp_path / 'settings.txt'
    path.write_text(json.dumps({
        'highscore_filename': 'scores.json',
        'levels': [{'width': 5, 'height': 5} for _ in range(10)],
    }), encoding='utf-8')
    return path


def test_terminal_win_name_save_and_return_to_menu(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """The public cheat and transition commands exercise the full CLI flow."""
    path = config_file(tmp_path)
    commands = ['s', *(['k', 'n'] * 9), 'k', 'Reviewer', 'h', 'q']
    with patch('builtins.input', side_effect=commands):
        assert cli_demo.main(['cli_demo', str(path)]) == 0
    output = capsys.readouterr().out
    assert 'Campaign won!' in output
    assert 'Level: 10/10' in output
    assert 'Score saved.' in output
    assert json.loads((tmp_path / 'scores.json').read_text()) == [
        ['Reviewer', 0],
    ]


def test_terminal_loss_also_offers_name_entry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """An actual last-life timeout enters the same score-submission flow."""
    path = config_file(tmp_path)
    state = GameState(make_config())
    state.lives = 1
    state.time_left = state.STEP_TIME
    with patch.object(cli_demo, 'GameState', return_value=state):
        with patch('builtins.input', side_effect=['s', '', 'Player', 'q']):
            assert cli_demo.main(['cli_demo', str(path)]) == 0
    assert state.status == 'game_over'
    assert 'Game over!' in capsys.readouterr().out
    stored = json.loads((tmp_path / 'scores.json').read_text())
    assert stored == [['Player', 0]]


def test_pause_blocks_movement_and_cheats_then_resumes() -> None:
    """Paused input cannot advance time, move, skip, or toggle protection."""
    with patch('pacman.game_state.build_grid', return_value=open_grid()):
        state = GameState(make_config())
    commands = ['p', 'k', 'd', 'i', 'p', 'i', 'd', 'q']
    with patch.object(cli_demo, 'GameState', return_value=state):
        with patch('builtins.input', side_effect=commands):
            assert cli_demo.play_campaign(state.config) is None
    assert state.level == 1
    assert state.status == 'playing'
    assert state.invisible
    assert state.player.pos == (3, 4)
    assert state.time_left == state.config.level_max_time - state.STEP_TIME


def test_nonqualifying_game_still_prompts_and_validates_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """Every completed game offers a name prompt, preserving top scores."""
    scores = Highscores(str(tmp_path / 'scores.json'))
    for number in range(10):
        assert scores.add(f'P{number}', 100 + number)
    previous = scores.top10()
    with patch('builtins.input', side_effect=['!', 'Player']) as prompt:
        cli_demo.submit_score(scores, 0)
        assert prompt.call_count == 2
    assert scores.top10() == previous
    assert 'does not enter the top ten' in capsys.readouterr().out


def test_save_failure_allows_retry_and_cancel(tmp_path: Path) -> None:
    """A failed persistence operation does not trap the name-entry loop."""
    scores = Highscores(str(tmp_path / 'scores.json'))
    with patch.object(scores, 'add', side_effect=[False, True]) as add:
        with patch('builtins.input', side_effect=['Player', 'Player']):
            cli_demo.submit_score(scores, 10)
        assert add.call_count == 2
    with patch('builtins.input', return_value=''):
        cli_demo.submit_score(scores, 10)
    assert scores.top10() == []


def test_relative_scores_resolve_beside_config(tmp_path: Path) -> None:
    """Launching from another cwd cannot silently select a different table."""
    path = config_file(tmp_path)
    scores = load_highscores(make_config(highscore_filename='scores.json'),
                             str(path))
    assert scores.add('Player', 10)
    assert (tmp_path / 'scores.json').is_file()


def test_root_launcher_accepts_arbitrary_config_filename(
    tmp_path: Path,
) -> None:
    """The subject's command accepts JSON content without a .json suffix."""
    path = config_file(tmp_path)
    result = subprocess.run(
        [sys.executable, str(ROOT / 'pac-man.py'), str(path)],
        input='q\n', capture_output=True, text=True, cwd=tmp_path, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert 'Traceback' not in result.stderr


@pytest.mark.parametrize('case', [
    'no_args', 'extra_args', 'missing', 'bad_json',
])
def test_root_launcher_reports_errors_without_tracebacks(
    tmp_path: Path, case: str,
) -> None:
    """Invalid startup arguments and files fail cleanly."""
    path = tmp_path / 'config'
    path.write_text('{invalid', encoding='utf-8')
    arguments = {
        'no_args': [], 'extra_args': [str(path), 'extra'],
        'missing': [str(tmp_path / 'absent')], 'bad_json': [str(path)],
    }[case]
    result = subprocess.run(
        [sys.executable, str(ROOT / 'pac-man.py'), *arguments],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0
    assert result.stderr.strip()
    assert 'Traceback' not in result.stderr


def test_generator_failure_is_reported_at_application_boundary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """The terminal stays friendly when the assigned generator fails."""
    path = config_file(tmp_path)
    with patch.object(cli_demo, 'GameState', side_effect=MazeError('failed')):
        with patch('builtins.input', return_value='s'):
            assert cli_demo.main(['cli_demo', str(path)]) == 1
    assert 'Error: failed' in capsys.readouterr().err


def test_unexpected_errors_and_eof_are_handled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """The last-resort handler reports bugs and EOF closes normally."""
    path = config_file(tmp_path)
    with patch('builtins.input', side_effect=RuntimeError('unexpected')):
        assert cli_demo.main(['cli_demo', str(path)]) == 1
    assert 'Unexpected game error: unexpected' in capsys.readouterr().err
    with patch('builtins.input', side_effect=EOFError):
        assert cli_demo.main(['cli_demo', str(path)]) == 0
