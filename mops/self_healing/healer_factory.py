from __future__ import annotations

from typing import TYPE_CHECKING

from mops.self_healing.config import get_config
from mops.self_healing.healer import Healer

if TYPE_CHECKING:
    from collections.abc import Callable

    from mops.self_healing.healer import FailedHealingResult, ScoringWeights
    from mops.self_healing.snapshot import SnapshotStorage


class _HealerState:
    """Module-level state for the healer singleton."""

    storage: SnapshotStorage | None = None
    score_threshold: float | None = None
    scoring_weights: ScoringWeights | None = None
    on_healing_failure: Callable[[FailedHealingResult], None] | None = None
    healer: Healer | None = None


def get_healer() -> Healer:
    """Return the global Healer singleton.

    Re-initialises when any healing-related config value changes so that
    ``configure()`` calls — including custom :class:`ScoringWeights` — between
    tests are picked up:

    * ``storage`` — identity check (and must not be ``None``)
    * ``score_threshold`` — value check
    * ``scoring_weights`` — identity check (mutating the same object in place
      works too, since the :class:`Healer` keeps a reference to it)
    * ``on_healing_failure`` — identity check
    """
    config = get_config()

    if (
        _HealerState.healer
        and _HealerState.storage is config.storage
        and _HealerState.storage is not None
        and _HealerState.score_threshold == config.score_threshold
        and _HealerState.scoring_weights is config.scoring_weights
        and _HealerState.on_healing_failure is config.on_healing_failure
    ):
        return _HealerState.healer

    _HealerState.storage = config.storage
    _HealerState.score_threshold = config.score_threshold
    _HealerState.scoring_weights = config.scoring_weights
    _HealerState.on_healing_failure = config.on_healing_failure
    _HealerState.healer = Healer(
        _HealerState.storage,
        config.score_threshold,
        scoring_weights=config.scoring_weights,
        on_healing_failure=config.on_healing_failure,
    )
    return _HealerState.healer
