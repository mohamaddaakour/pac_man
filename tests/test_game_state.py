"""A4-A8: timed movement, scoring, collisions, and campaign transitions."""

import pytest

import pacman.game_state as game_module
from pacman.entities import Direction, GhostState
from pacman.game_state import GameState
from pacman.maze_adapter import MazeError
from tests.core_helpers import make_config, open_grid, park_ghosts


@pytest.fixture
def state(monkeypatch: pytest.MonkeyPatch) -> GameState:
    """Use a known open room to isolate game rules from generation."""
    monkeypatch.setattr(game_module, 'build_grid', lambda *args: open_grid())
    return GameState(make_config())


def test_initial_pellets_and_public_campaign_length(state: GameState) -> None:
    """Every floor tile belongs to the player spawn or one pellet set."""
    floor = {(r, c) for r in range(1, 6) for c in range(1, 6)}
    assert state.pacgums | state.super_pacgums == floor - {state.player.pos}
    assert not state.pacgums & state.super_pacgums
    assert state.super_pacgums == set(state.ghost_spawns)
    assert state.total_levels == 10
    with pytest.raises(AttributeError):
        setattr(state, 'total_levels', 20)


def test_partial_steps_and_stopping_at_wall(state: GameState) -> None:
    """Movement uses elapsed time and never crosses a wall."""
    park_ghosts(state)
    state.set_direction(Direction.RIGHT)
    state.update(0.075)
    assert state.player.pos == (3, 3)
    state.update(0.075)
    assert state.player.pos == (3, 4)
    state.update(0.30)
    assert state.player.pos == (3, 5)
    assert state.player.direction is None


def test_buffered_turn_waits_until_corridor_opens(state: GameState) -> None:
    """A blocked turn stays buffered while forward movement continues."""
    park_ghosts(state)
    state.grid[2][1] = state.grid[2][2] = 1
    state.player.pos = (3, 1)
    state.player.direction = Direction.RIGHT
    state.set_direction(Direction.UP)
    state.update(0.15)
    assert state.player.pos == (3, 2)
    state.update(0.15)
    assert state.player.pos == (3, 3)
    state.update(0.15)
    assert state.player.pos == (2, 3)


def test_chunked_time_matches_one_update(state: GameState) -> None:
    """Different frame sizes produce the same uninterrupted movement."""
    other = GameState(state.config)
    for item in (state, other):
        park_ghosts(item)
        item.set_direction(Direction.RIGHT)
    state.update(0.45)
    for _ in range(45):
        other.update(0.01)
    assert state.player == other.player
    assert state.score == other.score
    assert state.time_left == pytest.approx(other.time_left)


def test_pacgum_scores_exactly_once(state: GameState) -> None:
    """Returning to an eaten pellet cannot increase the score again."""
    park_ghosts(state)
    for direction in (Direction.RIGHT, Direction.LEFT, Direction.RIGHT):
        state.set_direction(direction)
        state.update(0.15)
    assert state.score == state.config.points_per_pacgum
    assert (3, 4) not in state.pacgums


def test_power_pellet_protects_before_arrival_collision(
    state: GameState,
) -> None:
    """Eating a corner pellet turns its ghost edible before contact."""
    state.player.pos = (1, 2)
    state.set_direction(Direction.LEFT)
    state.update(0.15)
    assert state.lives == state.config.lives
    assert state.score == (
        state.config.points_per_super_pacgum + state.config.points_per_ghost
    )
    assert (1, 1) not in state.super_pacgums
    assert state.edible_timer == state.config.edible_duration
    assert state.ghosts[0].state == GhostState.EATEN
    assert all(g.state == GhostState.EDIBLE for g in state.ghosts[1:])
    score = state.score
    state.update(0)
    assert state.score == score


def test_eaten_ghost_waits_then_returns_normal(state: GameState) -> None:
    """Respawn finishes at the corner even while a power timer remains."""
    ghost = state.ghosts[0]
    ghost.state = GhostState.EATEN
    ghost.respawn_timer = 0.1
    state.edible_timer = 10.0
    state.update(0.05)
    assert ghost.state == GhostState.EATEN
    assert ghost.pos == state.ghost_spawns[0]
    state.update(0.05)
    assert state.ghosts[0].state == GhostState.NORMAL
    assert ghost.respawn_timer == 0
    assert ghost.movement_elapsed == 0


def test_edible_ghost_speed_and_power_expiry(state: GameState) -> None:
    """Edible movement is slower, and power expiration restores danger."""
    park_ghosts(state)
    ghost = state.ghosts[0]
    ghost.pos = (3, 4)
    ghost.state = GhostState.EDIBLE
    ghost.respawn_timer = 0
    state.edible_timer = 0.4
    state.update(0.2)
    assert ghost.pos == (3, 4)
    state.update(0.1)
    assert ghost.pos != (3, 4)
    state.update(0.1)
    assert ghost.state == GhostState.NORMAL
    assert state.edible_timer == 0


def test_multiple_contacts_cost_one_life_and_reset_entities(
    state: GameState,
) -> None:
    """One collision event resets the actors but preserves eaten pellets."""
    state.score = 17
    state.pacgums.remove((3, 4))
    for ghost in state.ghosts[:2]:
        ghost.pos = state.player.pos
    state.update(0)
    assert state.lives == state.config.lives - 1
    assert state.score == 17
    assert (3, 4) not in state.pacgums
    assert state.player.pos == state.player_spawn
    assert tuple(g.pos for g in state.ghosts) == state.ghost_spawns
    assert state.grace_timer == state.GRACE_DURATION


def test_arrival_contact_is_detected_before_ghost_moves(
    state: GameState,
) -> None:
    """A ghost due to move away cannot escape a player arrival collision."""
    state.ghosts[0].pos = (3, 4)
    state.ghosts[0].direction = Direction.LEFT
    state.ghosts[0].movement_elapsed = 0.05
    state.set_direction(Direction.RIGHT)
    state.update(0.15)
    assert state.lives == state.config.lives - 1


def test_swapped_tiles_are_a_collision(state: GameState) -> None:
    """The collision predicate recognizes actors crossing the same edge."""
    old_player = (3, 3)
    old_ghosts = ((3, 4), *state.ghost_spawns[1:])
    state.player.pos = (3, 4)
    state.ghosts[0].pos = old_player
    assert state._resolve_collisions(old_player, old_ghosts)
    assert state.lives == state.config.lives - 1


def test_invisibility_protects_one_hundred_contacts(state: GameState) -> None:
    """The reviewer cheat prevents normal-ghost damage until toggled off."""
    state.toggle_invisibility()
    for _ in range(100):
        state.ghosts[0].pos = state.player.pos
        state.update(0)
    assert state.lives == state.config.lives
    state.toggle_invisibility()
    state.update(0)
    assert state.lives == state.config.lives - 1


def test_grace_expiry_reenables_contact_damage(state: GameState) -> None:
    """Contact is safe during grace, then dangerous at the exact expiry."""
    state.grace_timer = 0.05
    state.ghosts[0].pos = state.player.pos
    state.update(0)
    assert state.lives == state.config.lives
    state.update(0.05)
    assert state.lives == state.config.lives - 1


def test_timeout_resets_timer_but_preserves_progress(state: GameState) -> None:
    """Timeout costs one life even when invisible, preserving this maze."""
    park_ghosts(state)
    state.invisible = True
    state.score = 50
    state.pacgums.remove((3, 4))
    grid = state.grid
    state.time_left = 0.01
    state.update(0.01)
    assert state.lives == state.config.lives - 1
    assert state.time_left == state.config.level_max_time
    assert state.grid is grid
    assert state.score == 50
    assert (3, 4) not in state.pacgums
    assert state.status == 'playing'


def test_last_life_timeout_ends_game(state: GameState) -> None:
    """The last timeout freezes the game without allowing negative lives."""
    state.lives = 1
    state.time_left = 0.01
    state.update(0.01)
    assert state.status == 'game_over'
    state.update(100)
    assert state.lives == 0
    assert state.time_left == 0


def test_last_pellet_wins_and_next_level_preserves_campaign(
    state: GameState,
) -> None:
    """Normal collection triggers completion and next_level resets timers."""
    park_ghosts(state)
    state.invisible = True
    state.pacgums = {(3, 4)}
    state.super_pacgums.clear()
    state.set_direction(Direction.RIGHT)
    state.update(0.15)
    assert state.status == 'level_won'
    score, lives = state.score, state.lives
    state.next_level()
    assert state.level == 2
    assert state.status == 'playing'
    assert (state.score, state.lives) == (score, lives)
    assert state.invisible
    assert state.time_left == state.config.level_max_time
    assert state.edible_timer == state.grace_timer == 0


def test_remaining_power_pellet_prevents_completion(state: GameState) -> None:
    """Both pellet sets must be empty before declaring a win."""
    park_ghosts(state)
    state.pacgums.clear()
    state.update(0.01)
    assert state.status == 'playing'


def test_skip_reaches_final_victory_without_awarding_points(
    state: GameState,
) -> None:
    """Ten deliberate skips exercise the public transition API."""
    state.score = 123
    for level in range(1, state.total_levels + 1):
        assert state.level == level
        state.skip_level()
        assert (state.score, state.lives) == (123, state.config.lives)
        if level < state.total_levels:
            assert state.status == 'level_won'
            state.next_level()
    assert state.status == 'game_won'


@pytest.mark.parametrize('status', ['level_won', 'game_won', 'game_over'])
def test_inactive_states_freeze_updates_and_ignore_skip(
    state: GameState, status: str,
) -> None:
    """Repeated input cannot bypass transitions or resurrect a lost game."""
    state.status = status
    before = (state.level, state.time_left, state.score, state.player.pos)
    state.update(10)
    state.skip_level()
    assert state.status == status
    assert before == (
        state.level, state.time_left, state.score, state.player.pos,
    )


@pytest.mark.parametrize('status', ['playing', 'game_won', 'game_over'])
def test_next_level_requires_cleared_nonfinal_level(
    state: GameState, status: str,
) -> None:
    """Invalid transition requests produce a clear error."""
    state.status = status
    with pytest.raises(ValueError, match='cleared non-final'):
        state.next_level()


def test_failed_transition_keeps_previous_state(
    state: GameState, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generator failure leaves the cleared level available for retry."""
    state.skip_level()
    grid, player = state.grid, state.player

    def fail(*args: object) -> list[list[int]]:
        """Simulate a broken assigned generator."""
        raise MazeError('generation failed')

    monkeypatch.setattr(game_module, 'build_grid', fail)
    with pytest.raises(MazeError, match='generation failed'):
        state.next_level()
    assert state.grid is grid
    assert state.player is player
    assert state.level == 1
    assert state.status == 'level_won'


@pytest.mark.parametrize('dt', [-1, float('nan'), float('inf')])
def test_invalid_time_is_rejected(state: GameState, dt: float) -> None:
    """Invalid elapsed time cannot corrupt timers or movement."""
    with pytest.raises(ValueError, match='finite and non-negative'):
        state.update(dt)
    assert state.time_left == state.config.level_max_time
