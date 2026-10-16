"""A8: campaign expansion, seed policy, and configuration immutability."""

import pytest

from pacman.config import LevelSpec
from pacman.levels import plan_levels


def test_campaign_expands_and_caps_growth() -> None:
    """Small configurations expand to ten progressively larger levels."""
    configured = (LevelSpec(15, 15, None), LevelSpec(17, 19, 123))
    plan = plan_levels(configured)
    assert len(plan) == 10
    assert plan[0] == LevelSpec(15, 15, 42)
    assert plan[1] == LevelSpec(17, 19, None)
    assert plan[2] == LevelSpec(19, 21, None)
    assert plan[-1] == LevelSpec(21, 21, None)
    assert all(level.seed is None for level in plan[1:])
    assert configured[0].seed is None
    assert configured[1].seed == 123


def test_large_custom_levels_are_not_shrunk() -> None:
    """The automatic growth cap does not discard larger custom sizes."""
    plan = plan_levels((LevelSpec(31, 25, 99),))
    assert plan[0].seed == 99
    assert all((level.width, level.height) == (31, 25) for level in plan)


def test_more_than_ten_configured_levels_are_preserved() -> None:
    """Ten is a minimum, not a maximum campaign length."""
    configured = tuple(LevelSpec(5 + i, 7, i) for i in range(12))
    plan = plan_levels(configured)
    assert len(plan) == 12
    assert [s.width for s in plan] == [s.width for s in configured]
    assert all(s.seed is None for s in plan[1:])


def test_empty_campaign_is_rejected() -> None:
    """The planner refuses an unvalidated empty configuration."""
    with pytest.raises(ValueError, match='at least one'):
        plan_levels(())
