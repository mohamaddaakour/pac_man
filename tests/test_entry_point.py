"""Tests for the graphical launcher (pac-man.py)."""

from __future__ import annotations

import functools
import importlib.util
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pygame
import pytest

import frontend.app
import frontend.window

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / 'pac-man.py'


def launch(
    *arguments: str, env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run pac-man.py like a player would and capture what it prints."""

    return subprocess.run(
        [sys.executable, str(LAUNCHER), *arguments],
        capture_output=True, text=True, cwd=ROOT, timeout=20, env=env,
    )


def launch_without(module: str) -> subprocess.CompletedProcess[str]:
    """Run pac-man.py as if `module` were not installed."""

    code = (
        f'import runpy, sys; sys.modules[{module!r}] = None; '
        f'sys.argv = ["pac-man.py", "config.json"]; '
        f'runpy.run_path({str(LAUNCHER)!r}, run_name="__main__")'
    )
    return subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True, text=True, cwd=ROOT, timeout=20,
    )


def last_line(result: subprocess.CompletedProcess[str]) -> str:
    """Return the final line written to stderr."""

    return result.stderr.strip().splitlines()[-1]


def assert_clean_failure(
    result: subprocess.CompletedProcess[str], expected: str,
) -> None:
    """A failure must be one readable line, never a traceback."""

    assert result.returncode == 1
    assert 'Traceback' not in result.stderr
    assert expected in last_line(result)


def config_file(tmp_path: Path, name: str = 'config.json') -> Path:
    """Write a valid config whose highscores stay in `tmp_path`."""

    path = tmp_path / name
    path.write_text('{"highscore_filename": "scores.json"}', encoding='utf-8')
    return path


@pytest.mark.parametrize('arguments', [[], ['a.json', 'b.json']])
def test_wrong_number_of_arguments_shows_usage(arguments: list[str]) -> None:
    assert_clean_failure(launch(*arguments), 'Usage: python3 pac-man.py')


@pytest.mark.parametrize('content, expected', [
    ('{ "lives": ', 'is not valid JSON'),
    ('[1, 2]', 'top level must be a JSON object'),
])
def test_invalid_config_files_are_reported(
    tmp_path: Path, content: str, expected: str,
) -> None:
    path = tmp_path / 'config.json'
    path.write_text(content, encoding='utf-8')

    assert_clean_failure(launch(str(path)), expected)


def test_missing_config_is_reported(tmp_path: Path) -> None:
    assert_clean_failure(
        launch(str(tmp_path / 'absent.json')), 'Config file not found',
    )


def test_directory_instead_of_config_is_reported(tmp_path: Path) -> None:
    assert_clean_failure(launch(str(tmp_path)), 'cannot read config file')


@pytest.mark.skipif(
    hasattr(os, 'geteuid') and os.geteuid() == 0,
    reason='root can read any file',
)
def test_unreadable_config_is_reported(tmp_path: Path) -> None:
    path = config_file(tmp_path)
    path.chmod(0)
    try:
        assert_clean_failure(launch(str(path)), 'cannot read config file')
    finally:
        path.chmod(0o644)


def test_no_display_is_reported() -> None:
    env = {
        key: value for key, value in os.environ.items()
        if key not in ('DISPLAY', 'WAYLAND_DISPLAY', 'SDL_VIDEODRIVER')
    }

    assert_clean_failure(
        launch('config.json', env=env), 'cannot open the game window',
    )


def test_config_name_does_not_need_a_json_suffix(tmp_path: Path) -> None:
    result = launch(str(config_file(tmp_path, 'settings')))

    # The config is accepted; only the missing display stops the game.
    assert_clean_failure(result, 'cannot open the game window')


@pytest.mark.parametrize('module', ['pygame', 'mazegenerator'])
def test_missing_package_is_named(module: str) -> None:
    assert_clean_failure(
        launch_without(module), f"missing package '{module}'",
    )


def errors(captured: str) -> list[str]:
    """Return stderr lines, without the core's tagged loading warnings."""

    return [line for line in captured.splitlines()
            if not line.startswith(('[config]', '[highscores]'))]


def load_launcher() -> ModuleType:
    """Import pac-man.py as a module (its name has a dash)."""

    spec = importlib.util.spec_from_file_location('pac_man', LAUNCHER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_game(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    play: Callable[[frontend.app.App], None],
) -> int:
    """Run main() headless, with `play` standing in for the game loop."""

    monkeypatch.setattr(
        frontend.window, 'Window',
        functools.partial(frontend.window.Window, headless_ok=True),
    )
    monkeypatch.setattr(frontend.app.App, 'run', play)
    arguments = ['pac-man.py', str(config_file(tmp_path))]
    try:
        code: int = load_launcher().main(arguments)
    except KeyboardInterrupt:
        # Left uncaught, pytest would take it for the user stopping the run.
        pytest.fail('KeyboardInterrupt escaped main()')
    return code


def test_quitting_the_game_exits_with_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def quit_at_once(app: frontend.app.App) -> None:
        """The player chooses EXIT right away."""

    assert run_game(tmp_path, monkeypatch, quit_at_once) == 0
    assert not pygame.display.get_init()


def test_ctrl_c_during_the_game_exits_quietly_with_130(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def interrupted(app: frontend.app.App) -> None:
        """Ctrl+C pressed in the terminal while playing."""
        raise KeyboardInterrupt

    assert run_game(tmp_path, monkeypatch, interrupted) == 130
    assert errors(capsys.readouterr().err) == []
    assert not pygame.display.get_init()


def test_unexpected_error_is_one_line_and_releases_the_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def crashing(app: frontend.app.App) -> None:
        """A bug inside the game loop."""
        raise RuntimeError('boom')

    assert run_game(tmp_path, monkeypatch, crashing) == 1
    assert errors(capsys.readouterr().err) == [
        'Unexpected error: RuntimeError: boom',
    ]
    assert not pygame.display.get_init()


def test_highscores_are_stored_beside_the_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def save_one(app: frontend.app.App) -> None:
        """Save a score the way the end screen does."""
        assert app.highscores.add('GM', 100)

    assert run_game(tmp_path, monkeypatch, save_one) == 0
    assert (tmp_path / 'scores.json').is_file()
