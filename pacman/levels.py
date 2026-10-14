from __future__ import annotations

# replace creates a new dataclass instance with selected fields changed.
# The original frozen instance remains unchanged.
from dataclasses import replace

from pacman.config import LevelSpec

MIN_LEVELS = 10

# Max maze size for width/height
AUTO_SIZE_CAP = 21


def plan_levels(configured: tuple[LevelSpec, ...]) -> tuple[LevelSpec, ...]:
    if not configured:
        raise ValueError("A campaign needs at least one configured level")

    levels = list(configured)

    # If the seed for the first level is None we have to make it always
    # the same and that by providing the same seed
    if levels[0].seed is None:
        levels[0] = replace(levels[0], seed=42)

    while len(levels) < MIN_LEVELS:
        previous = levels[-1]

        levels.append(LevelSpec(
            # Make the next level bigger if we can
            width=min(previous.width + 2, max(previous.width, AUTO_SIZE_CAP)),
            height=min(
                previous.height + 2, max(previous.height, AUTO_SIZE_CAP)
            ),
            seed=None,
        ))

    return tuple(levels)
