"""Demo: open a window, draw text and an image, close with Esc."""

from __future__ import annotations

import sys

from frontend.window import KEY_ESCAPE, GraphicsError, KeyEvent, Window

YELLOW = bytes((255, 220, 0, 255))
TRANSPARENT = bytes((0, 0, 0, 0))


def main() -> int:
    """Entry point"""

    try:
        with Window(400, 300, "Window demo") as window:
            # Left half opaque yellow, right half transparent.
            image = window.new_image(80, 80, False)
            image.pixels[:] = (YELLOW * 40 + TRANSPARENT * 40) * 80

            def draw(dt: float) -> None:
                window.clear((0, 0, 80))
                window.put_image(image, 160, 110)
                window.put_text(10, 10, "Esc or close button to quit",
                                (255, 255, 255))

            def handle_key(event: KeyEvent) -> None:
                if event.key_code == KEY_ESCAPE:
                    window.close()

            window.on_frame(draw)
            window.on_key(handle_key)
            window.run()
    except GraphicsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
