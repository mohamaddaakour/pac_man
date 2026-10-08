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
    """Create the map grid.
    
    Returns:
        `grid` where every 0's are the floor where pacman and ghosts can move
        and 1's are the walls
    """
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
                
    # Convert logical maze cells into game tiles, all slots with 1's.
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

            # For the last cell in the column there is an east wall open so we have to make it 0
            if col + 1 < width and not mask & 2:
                grid[tile_row][tile_col + 1] = 0

            # For the last cell in the row there is an south wall open so we have to make it 0
            if row + 1 < height and not mask & 4:
                grid[tile_row + 1][tile_col] = 0

    return grid


def is_connected(grid: Grid) -> bool:
    """Check if we can walk from any floor tile to any other floor tile"""
    if not grid or not grid[0]:
        return False
    
    # Get number of rows and cols
    rows: int = len(grid)
    cols: int = len(grid[0])

    # Check if it is a square map
    for row in grid:
        if len(row) != cols:
            return False
    
    # Check if tile is validated (int and between 0 and 1)
    for row in grid:
        for tile in row:
            if type(tile) is not int or tile not in (0, 1):
                return False
            
    
    corridors = {
        (row, col)
        for row in range(rows)
        for col in range(cols)
        if grid[row][col] == 0
    }

    if not corridors:
        return False

    center = (rows // 2, cols // 2)

    start = min(
        corridors,
        key=lambda pos: (
            abs(pos[0] - center[0]) + abs(pos[1] - center[1]),
            pos,
        ),
    )

    queue = deque([start])
    seen = {start}

    while queue:
        row, col = queue.popleft()

        for dr, dc in (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ):
            neighbor = (row + dr, col + dc)

            if neighbor in corridors and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)

    return seen == corridors


def _generate_cells(width: int, height: int, seed: int) -> object:
    """Call the external package without changing the game's random state."""

    # Save a snapshot of the global random state
    state = random.getstate()

    try:
        # Call the generator
        return MazeGenerator(
            size=(width, height),
            perfect=False,
            seed=seed,
        ).maze
    finally:
        # Always put the snapshot back
        random.setstate(state)


def build_grid(width: int, height: int, seed: int | None) -> Grid:
    """Generate a connected maze, trying at most six times."""

    if (
        type(width) is not int
        or type(height) is not int
        or not MIN_SIZE <= width <= MAX_SIZE
        or not MIN_SIZE <= height <= MAX_SIZE
    ):
        raise MazeError(
            f"Maze sides must be integers in {MIN_SIZE}-{MAX_SIZE}"
        )

    if seed is not None and type(seed) is not int:
        raise MazeError("Seed must be an integer or None")

    retry_rng = random.Random(seed)
    random_seed = random.SystemRandom()

    if seed is None:
        attempt_seed = random_seed.randint(1, MAX_SEED)
    else:
        # In case the seed is negative, this will happens: 1 + (--42 % MAX_SEED) = 1 + 42
        attempt_seed = seed if seed > 0 else 1 + (-seed % MAX_SEED)

    last_error: Exception | None = None

    for _ in range(MAX_ATTEMPTS):
        try:
            cells = _generate_cells(
                width,
                height,
                attempt_seed,
            )

        except Exception as exc:
            last_error = exc

        else:
            try:
                grid = _convert_cells(
                    cells,
                    width,
                    height,
                )

                if not is_connected(grid):
                    raise MazeError(
                        "Maze has empty or disconnected corridors"
                    )

                return grid

            except MazeError as exc:
                last_error = exc

        # Generate seed for next attempt.
        if seed is None:
            attempt_seed = random_seed.randint(
                1,
                MAX_SEED,
            )
        else:
            attempt_seed = retry_rng.randint(
                1,
                MAX_SEED,
            )

    raise MazeError(
        f"Cannot build {width}x{height} maze "
        f"after {MAX_ATTEMPTS} attempts: {last_error}"
    )