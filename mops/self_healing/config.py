from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from mops.self_healing.healer import FailedHealingResult, ScoringWeights, SuccessHealingResult
    from mops.self_healing.snapshot import SnapshotStorage


@dataclass
class SelfHealingConfig:
    """Configuration for self-healing locators.

    :param save_snapshots: When :obj:`True`, snapshots of successfully located elements
        are saved to storage for future healing.
    :param heal_locators: When :obj:`True`, the system attempts to heal broken locators
        by loading saved snapshots and searching for matching elements.
    :param score_threshold: Minimum similarity score (0-1) to accept a healed locator.
    :param scoring_weights: Tunable :class:`ScoringWeights` for element similarity scoring.
        Controls per-attribute, text, parent, and sibling contributions.
        When not set, built-in defaults are used.
    :param storage: A :class:`SnapshotStorage` instance. When not set, storage
        remains uninitialised and neither snapshots nor healing will work.
        External projects can pass their own backend (Redis, S3, PostgreSQL, etc.) here.
    :param on_healing_success: Optional callback invoked when a broken locator has been
        healed. Receives the :class:`SuccessHealingResult`.
    :param on_healing_failure: Optional callback invoked when healing was attempted
        but couldn't find a matching element. Receives the :class:`FailedHealingResult`.
    """

    save_snapshots: bool = False
    heal_locators: bool = False
    score_threshold: float = 0.7
    scoring_weights: ScoringWeights | None = None
    storage: SnapshotStorage | None = None
    on_healing_success: Callable[[SuccessHealingResult], None] | None = None
    on_healing_failure: Callable[[FailedHealingResult], None] | None = None


_config = SelfHealingConfig()


def configure(**kwargs: object) -> None:
    """Update the global self-healing config.

    Example::

        from mops.self_healing import configure, JsonFileSnapshotStorage

        # Save snapshots but don't heal (data collection)
        configure(save_snapshots=True)

        # Full healing: save snapshots AND heal broken locators
        configure(
            save_snapshots=True,
            heal_locators=True,
            score_threshold=0.75,
            storage=JsonFileSnapshotStorage('my_snapshots'),
        )

        # Custom backend
        configure(storage=MyCustomStorage())

        # Callbacks for external integrations
        def on_success(result: HealingResult) -> None:
            metrics.send(...)

        def on_failure(**kwargs: object) -> None:
            # kwargs: element_name, locator_key, locator
            post_comment_on_pr(kwargs['element_name'], kwargs['locator'])

        configure(
            save_snapshots=True,
            heal_locators=True,
            on_healing_success=on_success,
            on_healing_failure=on_failure,
        )
    """
    valid_fields = {f.name for f in dataclasses.fields(SelfHealingConfig)}
    for key, value in kwargs.items():
        if key not in valid_fields:
            msg = f"Unknown configuration key '{key}'. Valid fields: {sorted(valid_fields)}"
            raise ValueError(msg)
        setattr(_config, key, value)


def get_config() -> SelfHealingConfig:
    """Return the current global self-healing config."""
    return _config
