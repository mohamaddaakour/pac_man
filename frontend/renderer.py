"""Draw the maze, dots, sprites and HUD for each frame."""

from dataclasses import dataclass, replace
from frontend.window import Window, Image
from frontend.layout import Layout, compute_layout, to_pixels
from frontend.sprites import disc, pacman, ghost, eyes
from frontend.protocols import GameStateProtocol
from frontend.constants import (Color,
                                HUD_HEIGHT,
                                MAX_TILE,
                                BACKGROUND_COLOR,
                                WALL_COLOR,
                                CORRIDOR_COLOR,
                                PACGUM_COLOR,
                                SUPER_PACGUM_COLOR,
                                EDIBLE_COLOR,
                                EDIBLE_BLINK_COLOR,
                                GHOST_COLORS,
                                PACGUM_RADIUS,
                                SUPER_PACGUM_RADIUS,
                                MOUTH_PERIOD,
                                BLINK_START,
                                BLINK_PERIOD)
from pacman.entities import Direction, GhostState, Grid, Position


@dataclass
class _Level:
    """Everything built once per level and reused on every frame."""

    grid: Grid
    window_layout: Layout
    tile: int
    background: Image
    wall: bytes
    corridor: bytes
    pacgum_on_corridor: bytes
    super_pacgum_on_corridor: bytes
    drawn_pacgums: set[Position]
    drawn_super: set[Position]
    pacman_images: dict[tuple[Direction, bool], Image]
    ghosts: list[Image]
    edible_blue: Image
    edible_white: Image
    eyes_image: Image


class Renderer:
    """Draw the game state; images are built per level, not per frame."""

    def __init__(self, window: Window) -> None:
        """Start without a level; the first draw builds it."""
        self._window: Window = window
        self._clock: float = 0.0
        self._last_direction: Direction = Direction.RIGHT
        self._level: _Level | None = None

    def _put_tile(self,
                  background: Image,
                  tile: int,
                  row: int,
                  col: int,
                  pattern: bytes) -> None:
        """Copy a tile-sized pattern into the background, row by row."""
        for i in range(tile):
            current_row: int = i * tile * 4
            destination: int = (
                (i + row * tile) * background.width + col * tile
            ) * 4
            background.pixels[
                destination:destination + tile * 4
            ] = pattern[current_row:current_row + tile * 4]

    def _make_ghost_images(self, tile: int) -> list[Image]:
        """Build one ghost image per colour, in spawn-corner order."""
        ghost_images: list[Image] = []
        for ghost_color in GHOST_COLORS:
            ghost_image: Image = self._window.new_image(tile, tile, False)
            ghost_image.pixels[:] = ghost(tile, ghost_color)
            ghost_images.append(ghost_image)
        return ghost_images

    def _make_pacman_images(self,
                            tile: int) -> dict[tuple[Direction, bool], Image]:
        """Build Pac-Man for every direction, mouth open and closed."""
        pacman_images: dict[tuple[Direction, bool], Image] = {}
        for direction in Direction:
            for mouth_open in (True, False):
                pacman_image: Image = self._window.new_image(tile, tile, False)
                pacman_image.pixels[:] = pacman(
                    tile, direction, mouth_open)
                pacman_images[(direction, mouth_open)] = pacman_image
        return pacman_images

    def _make_pacgum_tile(self,
                          tile: int, radius: float, color: Color) -> bytes:
        """Return an opaque tile: a dot on the corridor colour.

        The background is RGBX and ignores alpha, so the transparent
        pixels of the dot must already hold the corridor colour.
        """
        pixels: bytearray = bytearray(
            disc(tile, tile * radius, color))
        for i in range(0, len(pixels), 4):
            if pixels[i + 3] == 0:
                for j in range(3):
                    pixels[i + j] = CORRIDOR_COLOR[j]
                pixels[i + 3] = 255
        return bytes(pixels)

    def _solid_tile(self, tile: int, color: Color) -> bytes:
        """Return a tile filled with one opaque colour."""
        pixel: bytes = bytes((*color, 255))
        return (pixel * (tile ** 2))

    def build_level(self, state: GameStateProtocol) -> None:
        """Compute the layout, then build the background and the sprites.

        The background holds the walls, the corridors and the dots, so a
        frame only draws one large image and five sprites.
        """
        rows, cols = len(state.grid), len(state.grid[0])
        old_layout: Layout = compute_layout(rows,
                                            cols,
                                            self._window.width,
                                            self._window.height - HUD_HEIGHT,
                                            MAX_TILE)
        window_layout: Layout = replace(
            old_layout,
            offset_y=old_layout.offset_y + HUD_HEIGHT)
        grid: Grid = state.grid
        tile: int = window_layout.tile
        wall: bytes = self._solid_tile(tile, WALL_COLOR)
        corridor: bytes = self._solid_tile(tile, CORRIDOR_COLOR)
        pacgum_on_corridor: bytes = self._make_pacgum_tile(
            tile,
            PACGUM_RADIUS,
            PACGUM_COLOR)
        super_pacgum_on_corridor: bytes = self._make_pacgum_tile(
            tile,
            SUPER_PACGUM_RADIUS,
            SUPER_PACGUM_COLOR)
        background: Image = self._window.new_image(cols * tile,
                                                   rows * tile,
                                                   True)
        for row in range(rows):
            for col in range(cols):
                if state.grid[row][col]:
                    self._put_tile(background, tile, row, col, wall)
                elif (row, col) in state.super_pacgums:
                    self._put_tile(
                        background, tile, row, col, super_pacgum_on_corridor)
                elif (row, col) in state.pacgums:
                    self._put_tile(
                        background, tile, row, col, pacgum_on_corridor)
                else:
                    self._put_tile(background, tile, row, col, corridor)
        drawn_pacgums: set[Position] = set(state.pacgums)
        drawn_super: set[Position] = set(state.super_pacgums)
        pacman_images: dict[
            tuple[Direction, bool], Image
        ] = self._make_pacman_images(tile)
        ghosts: list[Image] = self._make_ghost_images(tile)
        edible_blue: Image = self._window.new_image(tile, tile, False)
        edible_blue.pixels[:] = ghost(tile, EDIBLE_COLOR)
        edible_white: Image = self._window.new_image(tile, tile, False)
        edible_white.pixels[:] = ghost(tile, EDIBLE_BLINK_COLOR)
        eyes_image: Image = self._window.new_image(tile, tile, False)
        eyes_image.pixels[:] = eyes(tile)
        self._level = _Level(grid,
                             window_layout,
                             tile,
                             background,
                             wall,
                             corridor,
                             pacgum_on_corridor,
                             super_pacgum_on_corridor,
                             drawn_pacgums,
                             drawn_super,
                             pacman_images,
                             ghosts,
                             edible_blue,
                             edible_white,
                             eyes_image)

    def draw(self, state: GameStateProtocol, dt: float) -> None:
        """Draw one frame, rebuilding the level first if the grid is new.

        Eaten dots are painted over in the background and dots that came
        back are drawn again, by comparing with the dots drawn last time.

        Args:
            state: The game to draw.
            dt: Seconds since the last frame, used by the animations.
        """
        self._clock += dt
        if self._level is None or state.grid is not self._level.grid:
            self.build_level(state)
        level: _Level | None = self._level
        if level is None:
            raise RuntimeError("level has not been initialized")
        for eaten_pacgum in level.drawn_pacgums - state.pacgums:
            self._put_tile(level.background,
                           level.tile,
                           *eaten_pacgum,
                           level.corridor)
        for new_pacgum in state.pacgums - level.drawn_pacgums:
            self._put_tile(level.background,
                           level.tile,
                           *new_pacgum,
                           level.pacgum_on_corridor)
        level.drawn_pacgums = set(state.pacgums)
        for eaten_super in level.drawn_super - state.super_pacgums:
            self._put_tile(level.background,
                           level.tile,
                           *eaten_super,
                           level.corridor)
        for new_super in state.super_pacgums - level.drawn_super:
            self._put_tile(level.background,
                           level.tile,
                           *new_super,
                           level.super_pacgum_on_corridor)
        level.drawn_super = set(state.super_pacgums)
        self._window.clear(BACKGROUND_COLOR)
        x, y = to_pixels(level.window_layout, (0, 0))
        self._window.put_image(level.background, x, y)
        for index, _ghost in enumerate(state.ghosts):
            if _ghost.state == GhostState.EATEN:
                image: Image = level.eyes_image
            elif _ghost.state == GhostState.EDIBLE:
                blinking: bool = (state.edible_timer < BLINK_START
                                  and int(
                                      state.edible_timer / BLINK_PERIOD
                                      ) % 2 == 1)
                image = (level.edible_white
                         if blinking else level.edible_blue)
            elif _ghost.state == GhostState.NORMAL:
                image = level.ghosts[index]
            else:
                raise ValueError("invalid ghost state")
            x, y = to_pixels(level.window_layout, _ghost.pos)
            self._window.put_image(image, x, y)
        direction: Direction | None = state.player.direction
        mouth_open: bool = True
        if direction is not None:
            self._last_direction = direction
            if int(self._clock / MOUTH_PERIOD) % 2 != 0:
                mouth_open = False
        x, y = to_pixels(level.window_layout, state.player.pos)
        self._window.put_image(level.pacman_images[
            (self._last_direction, mouth_open)], x, y)
