"""Self-healing locators for MOPS.

Quick start::

    from mops.self_healing import configure, JsonFileSnapshotStorage
    configure(
        save_snapshots=True,
        heal_locators=True,
        score_threshold=0.75,
        storage=JsonFileSnapshotStorage(),
    )

Healing requires a :class:`SnapshotStorage` to be configured. The quickest way is::

    configure(
        save_snapshots=True,
        heal_locators=True,
        storage=JsonFileSnapshotStorage('my_snapshots'),
    )
"""

from mops.self_healing.config import configure, get_config
from mops.self_healing.healer import (
    FailedHealingResult,
    Healer,
    HealingStats,
    ScoringWeights,
    SuccessHealingResult,
    get_healing_stats,
)
from mops.self_healing.snapshot import ElementSnapshot, JsonFileSnapshotStorage, SnapshotStorage

__all__ = [
    'ElementSnapshot',
    'FailedHealingResult',
    'Healer',
    'HealingStats',
    'JsonFileSnapshotStorage',
    'ScoringWeights',
    'SnapshotStorage',
    'SuccessHealingResult',
    'configure',
    'get_config',
    'get_healing_stats',
]
