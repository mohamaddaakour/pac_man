"""Pac-Man game core, independent of graphics.

Shared conventions:
* Positions are (row, col) integer tuples; (0, 0) is the top-left tile.
* grid[row][col] is 0 for a corridor and 1 for a wall.
* Time and update(dt) intervals are measured in seconds, as floats.
* Directions use the Direction enum, never raw tuples.
"""
