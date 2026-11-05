"""Tests for the Linux package: the PyInstaller spec and the launcher."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / 'pac-man.spec'
LAUNCHER = ROOT / 'packaging' / 'run.sh'

# Stands in for the frozen game: prints its arguments, exits with 7.
FAKE_GAME = '#!/bin/sh\necho "$@"\nexit 7\n'


def fake_package(tmp_path: Path) -> Path:
    """Lay out a package whose game only prints its arguments."""

    package = tmp_path / 'pac-man-linux'
    (package / 'pac-man').mkdir(parents=True)
    shutil.copy(LAUNCHER, package / 'run.sh')
    game = package / 'pac-man' / 'pac-man'
    game.write_text(FAKE_GAME, encoding='utf-8')
    game.chmod(0o755)
    return package


def launch(
    package: Path, *arguments: str, cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Start the launcher with sh, as INSTRUCTIONS.txt tells players."""

    return subprocess.run(
        ['sh', str(package / 'run.sh'), *arguments],
        capture_output=True, text=True, cwd=cwd, timeout=20,
    )


def test_spec_builds_pac_man_py_into_one_folder() -> None:
    spec = SPEC.read_text(encoding='utf-8')

    assert "['pac-man.py']" in spec
    assert "name='pac-man'" in spec
    assert 'COLLECT(' in spec              # onedir: a folder, not one file
    assert 'upx=True' not in spec


def test_launcher_is_executable_in_the_repository() -> None:
    assert os.access(LAUNCHER, os.X_OK)


def test_launcher_uses_the_config_next_to_it_from_any_folder(
    tmp_path: Path,
) -> None:
    package = fake_package(tmp_path)
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()

    result = launch(package, cwd=elsewhere)

    assert Path(result.stdout.strip()).resolve() == \
        (package / 'config.json').resolve()
    assert result.returncode == 7          # the game's own exit code


def test_launcher_passes_the_players_config(tmp_path: Path) -> None:
    package = fake_package(tmp_path)

    result = launch(package, 'my.json', cwd=tmp_path)

    assert result.stdout.strip() == 'my.json'
    assert result.returncode == 7


def test_launcher_restores_a_lost_executable_bit(tmp_path: Path) -> None:
    package = fake_package(tmp_path)
    game = package / 'pac-man' / 'pac-man'
    game.chmod(0o644)                      # as some unzip tools leave it

    result = launch(package, cwd=tmp_path)

    assert result.returncode == 7
    assert game.stat().st_mode & stat.S_IXUSR
