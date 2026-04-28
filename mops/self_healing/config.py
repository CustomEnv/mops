from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SelfHealingConfig:
    """Configuration for self-healing locators.

    :param enabled: Enable or disable self-healing globally.
    :param score_threshold: Minimum similarity score (0–1) to accept a healed locator.
    :param storage_path: Path to the SQLite database for storing element snapshots.
    """

    enabled: bool = False
    score_threshold: float = 0.7
    storage_path: str = '.self_healing.db'


_config = SelfHealingConfig()


def configure(**kwargs: object) -> None:
    """Update the global self-healing config.

    Example::

        from mops.self_healing import configure
        configure(enabled=True, score_threshold=0.8)
    """
    for key, value in kwargs.items():
        setattr(_config, key, value)


def get_config() -> SelfHealingConfig:
    """Return the current global self-healing config."""
    return _config
