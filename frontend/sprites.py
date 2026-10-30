"""Build sprite pixels (Pac-Man, ghosts, dots) for a given tile size."""

import math
from frontend.constants import PACMAN_COLOR, EYES_COLOR, Color
from pacman.entities import Direction


def disc(size: int, radius: float, color: Color) -> bytes:
    """Return RGBA pixels of a filled disc centred in a size x size
    tile. The radius is at least 0.75 px so tiny tiles still show it.
    """
    pixels: bytearray = bytearray((size ** 2) * 4)
    center: float = (size - 1) / 2
    effective_radius: float = max(radius, 0.75)
    for y in range(size):
        for x in range(size):
            square_distance: float = (x - center) ** 2 + (y - center) ** 2
            if square_distance > effective_radius ** 2:
                continue
            index: int = (y * size + x) * 4
            for i in range(3):
                pixels[index + i] = color[i]
            pixels[index + 3] = 255
    return bytes(pixels)


def pacman(size: int, direction: Direction, mouth_open: bool) -> bytes:
    """Return RGBA pixels of Pac-Man.

    Args:
        size: Tile size in pixels.
        direction: Direction the mouth faces.
        mouth_open: Cut a 70 degree wedge for the mouth.
    """
    pixels: bytearray = bytearray((size ** 2) * 4)
    center: float = (size - 1) / 2
    radius: float = size / 2 - 1
    angle: float = math.atan2(direction.dr, direction.dc)
    for y in range(size):
        for x in range(size):
            square_distance: float = (x - center) ** 2 + (y - center) ** 2
            if square_distance > radius ** 2:
                continue
            pixel_angle: float = math.atan2(y - center, x - center)
            delta: float = math.atan2(
                math.sin(pixel_angle - angle),
                math.cos(pixel_angle - angle)
            )
            if (mouth_open and abs(delta) <= 35 * math.pi / 180):
                continue
            index: int = (y * size + x) * 4
            for i in range(3):
                pixels[index + i] = PACMAN_COLOR[i]
            pixels[index + 3] = 255
    return bytes(pixels)


def ghost(size: int, color: Color) -> bytes:
    """Return RGBA pixels of a ghost: rounded top, wavy skirt."""
    pixels: bytearray = bytearray((size ** 2) * 4)
    center: float = (size - 1) / 2
    radius: float = size / 2 - 1
    amplitude: float = size / 12
    base_y: float = size - 1 - amplitude
    for y in range(size):
        for x in range(size):
            square_distance: float = (
                x - center) ** 2 + (y - center) ** 2
            bottom_y: float = base_y - amplitude * math.cos(
                (2 * math.pi * 3 * (x - center)) / size
            )
            rounded_top: bool = (
                square_distance <= radius ** 2 and y <= center
            )
            rectangular_lower_body: bool = (
                center < y < bottom_y and abs(x - center) <= radius
            )
            inside_ghost: bool = rounded_top or rectangular_lower_body
            if not inside_ghost:
                continue
            index: int = (y * size + x) * 4
            for i in range(3):
                pixels[index + i] = color[i]
            pixels[index + 3] = 255
    return bytes(pixels)


def eyes(size: int) -> bytes:
    """Return RGBA pixels of two eyes, drawn over every ghost.

    An eaten ghost shows only its eyes.
    """
    pixels: bytearray = bytearray((size ** 2) * 4)
    center: float = (size - 1) / 2
    eye_y: float = (2 * size) / 5
    left_eye_x: float = center - size / 6
    right_eye_x: float = center + size / 6
    eye_radius_x: float = size / 10
    eye_radius_y: float = size / 5
    for y in range(size):
        for x in range(size):
            in_left_eye: bool = (
                (x - left_eye_x) ** 2
            ) / (eye_radius_x ** 2) + (
                (y - eye_y) ** 2) / (
                    eye_radius_y ** 2
                ) <= 1
            in_right_eye: bool = (
                (x - right_eye_x) ** 2
            ) / (eye_radius_x ** 2) + (
                (y - eye_y) ** 2) / (
                    eye_radius_y ** 2
                ) <= 1
            in_eye: bool = in_left_eye or in_right_eye
            if not in_eye:
                continue
            index: int = (y * size + x) * 4
            for i in range(3):
                pixels[index + i] = EYES_COLOR[i]
            pixels[index + 3] = 255
    return bytes(pixels)


def scale_up(pixels: bytes, width: int, height: int, factor: int) -> bytes:
    """Return the RGBA image `factor` times bigger.

    Each pixel becomes a factor x factor block (nearest neighbour).
    """
    output_buffer: bytearray = bytearray(height * width * (factor ** 2) * 4)
    for y in range(height * factor):
        for x in range(width * factor):
            source_x: int = x // factor
            source_y: int = y // factor
            source_index: int = (source_y * width + source_x) * 4
            output_index: int = (y * width * factor + x) * 4
            for i in range(4):
                output_buffer[output_index + i] = pixels[source_index + i]
    return bytes(output_buffer)
