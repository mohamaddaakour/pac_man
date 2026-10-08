"""Pytest setup: run pygame headless with the SDL dummy video driver."""

import os

import pytest

# Must run before pygame is imported or a window is created.
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'


def pytest_configure(config: pytest.Config) -> None:
    """Hide deprecation warnings from pygame's use of pkg_resources.

    They come from third-party code, not from this project.
    """

    config.addinivalue_line(
        'filterwarnings',
        'ignore:pkg_resources is deprecated:DeprecationWarning',
    )
    config.addinivalue_line(
        'filterwarnings', 'ignore::DeprecationWarning:pkg_resources',
    )
