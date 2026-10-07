from __future__ import annotations

import random
from collections import deque

from mazegenerator import MazeGenerator

from pacman.config import MAX_SIZE, MIN_SIZE

Grid = list[list[int]]
Position = tuple[int, int]
MAX_ATTEMPTS = 6

# The largest signed int
MAX_SEED = 2**31 - 1


class MazeError(Exception):
    """Maze generation failed."""


def _convert_cells(cells: list[list[int]], width: int, height: int) -> Grid:
    if not isinstance(cells, list) or len(cells) != height:
        raise MazeError("Generator returned the wrong number of rows")
    
    masks: list[list[int]] = []

    for row in cells:
        if not isinstance(row, list) or len(row) != width:
            raise MazeError("Generator returned the wrong sized of row")
        
        checked: list[int] = []


        for mask in row:
            if type(mask) != int or not 0 <= mask <= 15:
                raise MazeError("Wall masks must be integers from 0 to 15")
            
            checked.append(mask)
        
        masks.append(checked)

    for row in range(height):
        for col in range(width):
            mask = masks[row][col]

            if (
                # Check are we in the top row and is the north wall missing
                row == 0 and not mask & 1
            ) or (
                # Check are we int the last row and if the south wall missing
                row == height - 1 and not mask & 4
            ):
                raise MazeError("Exterior north/south wall is open")
            
            if (
                # Check are we in the first col and the east wall missing
                col == 0 and not mask & 8
            ) or (
                # Check are we in the bottom col and the west wall missing
                col == width - 1 and not mask & 2
            ):
                raise MazeError("Generator opened an exterior east/west wall")
            
            # East/West neighboring walls must agree.
            if col + 1 < width:
                if bool(mask & 2) != bool(masks[row][col + 1] & 8):
                    raise MazeError("Neighboring east/west walls disagree")

            # North/South neighboring walls must agree.
            if row + 1 < height:
                if bool(mask & 4) != bool(masks[row + 1][col] & 1):
                    raise MazeError("Neighboring north/south walls disagree")
                
    # Convert logical maze cells into game tiles.
    grid = [
        [1] * (2 * width + 1)
        for _ in range(2 * height + 1)
    ]

    for row in range(height):
        for col in range(width):
            mask = masks[row][col]

            # Fully enclosed cells remain blocked.
            if mask == 15:
                continue

            tile_row = 2 * row + 1
            tile_col = 2 * col + 1

            grid[tile_row][tile_col] = 0

            # East opening
            if col + 1 < width and not mask & 2:
                grid[tile_row][tile_col + 1] = 0

            # South opening
            if row + 1 < height and not mask & 4:
                grid[tile_row + 1][tile_col] = 0

    return grid