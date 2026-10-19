"""Layout math: tile size, maze offsets and (row, col) to pixel (x, y)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Layout:
    """Tile size and top-left offset of the maze, in pixels."""

    tile: int
    offset_x: int
    offset_y: int


def compute_layout(rows: int,
                   cols: int,
                   area_width: int,
                   area_height: int,
                   max_tile: int) -> Layout:
    """Pick the largest tile size that fits the maze, then centre it.

    Args:
        rows: Number of tile rows in the maze.
        cols: Number of tile columns in the maze.
        area_width: Width of the drawing area in pixels.
        area_height: Height of the drawing area in pixels.
        max_tile: Largest allowed tile size in pixels.

    Returns:
        The tile size and the maze offsets inside the area.

    Raises:
        ValueError: A parameter is not positive, or the maze is
            too large for the area.
    """
    if not (rows > 0
            and cols > 0
            and area_width > 0
            and area_height > 0
            and max_tile > 0):
        raise ValueError("parameters should be strictly positive")
    tile: int = min(area_width // cols, area_height // rows, max_tile)
    if tile < 1:
        raise ValueError("maze cannot fit in the available area")
    maze_width: int = cols * tile
    maze_height: int = rows * tile
    offset_x: int = (area_width - maze_width) // 2
    offset_y: int = (area_height - maze_height) // 2
    return Layout(tile, offset_x, offset_y)


def to_pixels(layout: Layout, pos: tuple[int, int]) -> tuple[int, int]:
    """Return the (x, y) pixel of the top-left corner of tile
    (row, col); x comes from the column and y from the row.
    """
    x: int = layout.offset_x + pos[1] * layout.tile
    y: int = layout.offset_y + pos[0] * layout.tile
    return (x, y)
