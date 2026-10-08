"""Window wrapper: the only module using pygame, with MLX-like calls."""

import time
from dataclasses import dataclass
from types import TracebackType
from typing import Callable, Literal

import pygame

KEY_ESCAPE: int = pygame.K_ESCAPE


class GraphicsError(Exception):
    """The window cannot be created, or an image size is invalid."""
    pass


@dataclass
class Image:
    """A pixel buffer and the pygame surface that shares its memory.

    Equivalent to mlx_new_image + mlx_get_data_addr: writing into
    `pixels` changes what is drawn.
    """
    pixels: bytearray
    surface: pygame.Surface
    width: int
    height: int


@dataclass
class KeyEvent:
    """A key press: key code, physical scan code and typed character."""
    key_code: int
    scan_code: int
    typed_character: str


class Window:
    """Game window with MLX-like calls; the only user of pygame."""

    def __init__(self,
                 width: int,
                 height: int,
                 title: str,
                 headless_ok: bool = False
                 ) -> None:
        """Open the window.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            title: Window title.
            headless_ok: Accept a driver without a display (tests only).

        Raises:
            GraphicsError: No display, or the window cannot be created.
        """
        try:
            self.width: int = width
            self.height: int = height
            self.title: str = title
            try:
                pygame.display.init()
            except pygame.error as exc:
                raise GraphicsError(exc) from exc
            pygame.font.init()
            driver: str = pygame.display.get_driver()
            if driver in ("offscreen", "dummy") and not headless_ok:
                raise GraphicsError("no display found")
            try:
                self.screen: pygame.Surface = pygame.display.set_mode(
                    (self.width, self.height)
                )
            except pygame.error as exc:
                raise GraphicsError(exc) from exc
            pygame.display.set_caption(self.title)
            self.font: pygame.font.Font = pygame.font.Font(None, 24)
            self.closed: bool = False
            self.key_callback: Callable[[KeyEvent], None] | None = None
            self.close_callback: Callable[[], None] | None = None
            self.frame_callback: Callable[[float], None] | None = None
        except Exception:
            pygame.quit()
            raise

    def new_image(self, width: int, height: int, opaque: bool) -> Image:
        """Create an image whose pixels live in a bytearray (4 bytes each).

        Args:
            width: Width in pixels.
            height: Height in pixels.
            opaque: True for RGBX (no transparency), False for RGBA.

        Raises:
            GraphicsError: `width` or `height` is not positive.
        """
        if not (width > 0 and height > 0):
            raise GraphicsError("width and height should be strictly positive")
        pixels: bytearray = bytearray(width * height * 4)
        format_name: Literal["RGBX", "RGBA"]
        if opaque:
            format_name = "RGBX"
        else:
            format_name = "RGBA"
        surface: pygame.Surface = pygame.image.frombuffer(
            pixels, (width, height), format_name
        )
        return Image(pixels, surface, width, height)

    def put_image(self, image: Image, x: int, y: int) -> None:
        """Draw `image` with its top-left corner at (x, y)."""
        self.screen.blit(image.surface, (x, y))

    def clear(self, color: tuple[int, ...]) -> None:
        """Fill the whole window with `color`."""
        self.screen.fill(color)

    def put_text(self, x: int, y: int, text: str, color: tuple[int, ...]
                 ) -> None:
        """Draw `text` in `color` with its top-left corner at (x, y)."""
        self.screen.blit(self.font.render(text, False, color), (x, y))

    def on_key(self, cb: Callable[[KeyEvent], None]) -> None:
        """Call `cb` with a KeyEvent for every key press."""
        self.key_callback = cb

    def on_close(self, cb: Callable[[], None]) -> None:
        """Call `cb` when the close button of the window is clicked."""
        self.close_callback = cb

    def on_frame(self, cb: Callable[[float], None]) -> None:
        """Call `cb` once per frame with the seconds since the last frame."""
        self.frame_callback = cb

    def close(self) -> None:
        """Stop the loop at the end of the current frame."""
        self.closed = True

    def run(self) -> None:
        """Run the main loop until `close()`, then release pygame.

        Each frame: dispatch events, call the frame callback with dt
        (capped at 0.1 s), show the frame, then wait to keep ~60 FPS.
        """
        try:
            previous_time: float = time.monotonic()
            while not self.closed:
                now: float = time.monotonic()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        if self.close_callback is not None:
                            self.close_callback()
                        self.close()
                        break
                    elif event.type == pygame.KEYDOWN:
                        key: int = event.key
                        scancode: int = event.scancode
                        character: str = event.unicode
                        key_event = KeyEvent(key, scancode, character)
                        if self.key_callback is not None:
                            self.key_callback(key_event)
                dt: float = min(now - previous_time, 0.1)
                previous_time = now
                if self.frame_callback is not None:
                    self.frame_callback(dt)
                pygame.display.flip()
                elapsed: float = time.monotonic() - now
                if (1 / 60 - elapsed) > 0:
                    time.sleep(1 / 60 - elapsed)
        finally:
            pygame.quit()

    def __enter__(self) -> "Window":
        """Return the window for use in a `with` block."""
        return self

    def __exit__(self,
                 exc_type: type[BaseException] | None,
                 exc_value: BaseException | None,
                 traceback: TracebackType | None
                 ) -> None:
        """Stop the loop and release pygame."""
        self.close()
        pygame.quit()
