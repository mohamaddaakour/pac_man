"""A8 acceptance: collect every pellet across ten generated levels."""

from collections import deque

from pacman.config import LevelSpec
from pacman.entities import Direction, Position, is_walkable
from pacman.game_state import GameState
from tests.core_helpers import make_config


def direction_to_next_pellet(state: GameState) -> Direction:
    """Use BFS only as a test driver to select the next player input."""
    remaining = state.pacgums | state.super_pacgums
    queue: deque[tuple[Position, Direction | None]] = deque([
        (state.player.pos, None),
    ])
    seen = {state.player.pos}
    while queue:
        pos, first = queue.popleft()
        if pos in remaining and first is not None:
            return first
        for direction in Direction:
            target = pos[0] + direction.dr, pos[1] + direction.dc
            if target not in seen and is_walkable(state.grid, target):
                seen.add(target)
                queue.append((target, first or direction))
    raise AssertionError('No remaining pellet is reachable')


def test_collect_all_pellets_through_ten_real_levels() -> None:
    """Actual movement and collection reach victory without skip_level."""
    config = make_config(
        levels=tuple(LevelSpec(5, 5, None) for _ in range(10)),
        level_max_time=600.0,
    )
    state = GameState(config)
    state.toggle_invisibility()
    previous_score = 0
    for level in range(1, 11):
        assert state.level == level
        for _ in range(1000):
            state.set_direction(direction_to_next_pellet(state))
            state.update(state.STEP_TIME)
            assert state.score >= previous_score
            previous_score = state.score
            if state.status != 'playing':
                break
        assert not state.pacgums and not state.super_pacgums
        assert state.lives == config.lives
        if level < 10:
            assert state.status == 'level_won'
            state.next_level()
            assert state.score == previous_score
            assert state.time_left == config.level_max_time
    assert state.status == 'game_won'
