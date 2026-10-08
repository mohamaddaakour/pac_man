"""Tests for the pygame window wrapper (frontend.window)."""

from __future__ import annotations

from collections.abc import Iterator

import pygame
import pytest

from frontend.window import GraphicsError, KeyEvent, Window


@pytest.fixture
def window() -> Iterator[Window]:
    """Open a headless window and always shut pygame down afterwards."""

    win = Window(64, 48, 'test', headless_ok=True)
    yield win
    pygame.quit()


def run_frames(window: Window, limit: int) -> list[float]:
    """Run the loop for at most `limit` frames and return the dt values."""

    dts: list[float] = []

    def frame(dt: float) -> None:
        dts.append(dt)
        if len(dts) >= limit:
            window.close()

    window.on_frame(frame)
    window.run()

    return dts


def screen() -> pygame.Surface:
    """Return the window surface."""

    surface = pygame.display.get_surface()
    assert surface is not None

    return surface


def test_window_opens_headless(window: Window) -> None:
    assert screen().get_size() == (64, 48)
    assert pygame.display.get_caption()[0] == 'test'


def test_no_display_is_refused_and_pygame_released() -> None:
    with pytest.raises(GraphicsError, match='no display'):
        Window(64, 48, 'test')
    assert not pygame.display.get_init()


@pytest.mark.parametrize('width, height', [(0, 5), (5, 0), (-1, 5)])
def test_new_image_refuses_bad_sizes(
    window: Window, width: int, height: int,
) -> None:
    with pytest.raises(GraphicsError):
        window.new_image(width, height, False)


def test_image_shares_its_pixel_buffer(window: Window) -> None:
    image = window.new_image(2, 1, False)
    image.pixels[0:4] = bytes((255, 0, 0, 255))

    assert tuple(image.surface.get_at((0, 0))) == (255, 0, 0, 255)


def test_transparent_pixels_keep_the_background(window: Window) -> None:
    image = window.new_image(2, 1, False)
    image.pixels[0:4] = bytes((255, 0, 0, 255))  # second pixel: alpha 0

    window.clear((0, 0, 40))
    window.put_image(image, 10, 10)

    assert tuple(screen().get_at((10, 10)))[:3] == (255, 0, 0)
    assert tuple(screen().get_at((11, 10)))[:3] == (0, 0, 40)


def test_opaque_image_hides_the_background(window: Window) -> None:
    image = window.new_image(4, 4, True)

    window.clear((255, 0, 0))
    window.put_image(image, 0, 0)

    assert tuple(screen().get_at((2, 2)))[:3] == (0, 0, 0)


def test_put_text_draws_pixels(window: Window) -> None:
    window.clear((0, 0, 0))
    window.put_text(0, 0, 'HI', (255, 255, 255))

    assert any(
        tuple(screen().get_at((x, y)))[:3] != (0, 0, 0)
        for x in range(30) for y in range(30)
    )


def test_dt_is_time_since_previous_frame(window: Window) -> None:
    dts = run_frames(window, 6)

    # The loop is capped at about 60 frames per second.
    assert all(0.01 < dt < 0.5 for dt in dts[1:])


def test_close_ends_run_and_quits_pygame(window: Window) -> None:
    assert len(run_frames(window, 3)) == 3
    assert not pygame.display.get_init()


def test_close_twice_is_harmless(window: Window) -> None:
    window.close()
    window.close()
    window.run()

    assert not pygame.display.get_init()


def test_exception_in_callback_propagates_and_quits_pygame(
    window: Window,
) -> None:
    def frame(dt: float) -> None:
        raise ValueError('boom')

    window.on_frame(frame)
    with pytest.raises(ValueError, match='boom'):
        window.run()
    assert not pygame.display.get_init()


def test_quit_event_calls_close_callback_and_stops(window: Window) -> None:
    closed: list[bool] = []
    window.on_close(lambda: closed.append(True))
    pygame.event.post(pygame.event.Event(pygame.QUIT))

    assert len(run_frames(window, 100)) < 100
    assert closed == [True]


def test_key_events_reach_the_key_callback(window: Window) -> None:
    received: list[KeyEvent] = []
    window.on_key(received.append)
    pygame.event.post(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_a, scancode=pygame.KSCAN_A,
        unicode='a', mod=0,
    ))

    run_frames(window, 2)

    assert received == [KeyEvent(pygame.K_a, pygame.KSCAN_A, 'a')]


def test_with_block_releases_pygame_without_run() -> None:
    with Window(64, 48, 'test', headless_ok=True):
        pass
    assert not pygame.display.get_init()
