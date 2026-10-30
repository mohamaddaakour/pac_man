"""BFS-based decisions for chasing and fleeing without wall collisions."""

from __future__ import annotations

import random
from collections import deque

from pacman.entities import (
    Direction, Ghost, GhostState, Grid, Position, is_walkable,
)

# At junctions, 70% selects the chase branch; random picks may also be best.
CHASE_CHANCE = 0.70

# Read the direction offsets once instead of resolving properties per tile.
STEPS = tuple(direction.value for direction in Direction)


# BFS implementation
def distance_map(grid: Grid, goal: Position) -> dict[Position, int]:
    """Return shortest corridor distances to goal using one BFS."""
    if not is_walkable(grid, goal):
        return {}

    distances = {goal: 0}
    queue = deque([goal])
    rows = len(grid)

    while queue:
        row, col = queue.popleft()
        next_distance = distances[(row, col)] + 1
        for dr, dc in STEPS:
            nr, nc = row + dr, col + dc
            if not (0 <= nr < rows and 0 <= nc < len(grid[nr])):
                continue
            neighbor = (nr, nc)

            if neighbor not in distances and grid[nr][nc] == 0:
                distances[neighbor] = next_distance
                queue.append(neighbor)

    return distances


def choose_direction(
    grid: Grid, ghost: Ghost, distances: dict[Position, int],
    rng: random.Random,
) -> Direction | None:
    """Chase normally, flee when edible, and reverse only at dead ends.

    At junctions a normal ghost uses the shortest allowed move 70% of the
    time and a random allowed move otherwise. Ties follow Direction order.
    The random branch may also pick the shortest move.
    """
    # Eaten ghosts wait to respawn; unreachable ghosts cannot move.
    if ghost.state == GhostState.EATEN or ghost.pos not in distances:
        return None

    # At the player tile, resolve contact before requesting movement.
    if distances[ghost.pos] == 0:
        return None

    row, col = ghost.pos

    # the walkable directions
    neighbors = [
        direction for direction in Direction
        if is_walkable(grid, (row + direction.dr, col + direction.dc))
        and (row + direction.dr, col + direction.dc) in distances
    ]

    if not neighbors:
        return None

    # Remove the reverse move if another walkable option exists.
    candidates = neighbors

    if ghost.direction is not None:
        forward_options = [
            direction for direction in neighbors
            if (direction.dr, direction.dc) != (
                -ghost.direction.dr, -ghost.direction.dc
            )
        ]
        if forward_options:
            candidates = forward_options

    def distance(direction: Direction) -> int:
        """Look up the BFS distance at a candidate destination."""
        return distances[(row + direction.dr, col + direction.dc)]

    if ghost.state == GhostState.EDIBLE:
        return max(candidates, key=distance)

    best = min(candidates, key=distance)

    if len(neighbors) >= 3 and len(candidates) > 1:
        if rng.random() >= CHASE_CHANCE:
            # Choose randomly
            return rng.choice(candidates)

    return best
