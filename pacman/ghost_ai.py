"""BFS-based decisions for chasing and fleeing without wall collisions."""

from __future__ import annotations

import random
from collections import deque

from pacman.entities import (
    Direction, Ghost, GhostState, Grid, Position, is_walkable,
)

# A normal ghost takes the best move 70% of the time.
CHASE_CHANCE = 0.70


# BFS implementation
def distance_map(grid: Grid, goal: Position) -> dict[Position, int]:
    """Return shortest corridor distances to goal using one BFS."""
    if not is_walkable(grid, goal):
        return {}

    distances = {goal: 0}
    queue = deque([goal])

    while queue:
        row, col = queue.popleft()
        for direction in Direction:
            neighbor = row + direction.dr, col + direction.dc

            if neighbor not in distances and is_walkable(grid, neighbor):
                distances[neighbor] = distances[(row, col)] + 1
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
    # If the ghost is eaten it will flee not chase
    if ghost.state == GhostState.EATEN or ghost.pos not in distances:
        return None

    # distance = 0 means pacman position and the collision function will handle this
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