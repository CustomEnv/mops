from __future__ import annotations

from unittest.mock import MagicMock, patch

import mops.self_healing.healer as healer_module
from mops.self_healing.healer import HealingStats, get_healing_stats
from mops.self_healing.snapshot import ElementSnapshot


def _make_snapshot(**overrides: str) -> ElementSnapshot:
    """Build an ElementSnapshot with sensible defaults."""
    defaults = dict(
        tag='button',
        attributes={'id': 'submit'},
        text='Click',
        parent_tag='form',
        parent_attributes={},
        siblings=[],
    )
    defaults.update(overrides)
    return ElementSnapshot(**defaults)


def _make_candidate(index: int = 0, **extra: str) -> dict:
    """Build a candidate dict with values matching the default snapshot."""
    return {
        'index': index,
        'attrs': {'id': 'submit'},
        'text': 'Click',
        'parentTag': 'form',
        'parentAttrs': {},
        **extra,
    }


def _fresh_stats(monkeypatch) -> HealingStats:
    """Replace the module-level stats with a clean instance for the test."""
    stats = HealingStats()
    monkeypatch.setattr(healer_module, '_stats', stats)
    return stats


def test_get_healing_stats_returns_live_stats(monkeypatch):
    """get_healing_stats() returns the same object the Healer records into."""
    stats = _fresh_stats(monkeypatch)
    assert get_healing_stats() is stats


def test_stats_count_successful_heal(monkeypatch):
    """A successful heal() increments attempts and healed, and records a score."""
    stats = _fresh_stats(monkeypatch)
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.return_value = [_make_candidate()]
    driver.driver.find_elements.return_value = [MagicMock()]
    healer = healer_module.Healer(storage, 0.7)

    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        assert healer.heal('btn', 'key', '#submit', driver) is not None

    assert stats.attempts == 1
    assert stats.healed == 1
    assert stats.failed == 0
    assert stats.failed_reasons == {}
    assert stats.avg_best_score is not None
    assert 0.0 < stats.avg_best_score <= 1.0


def test_stats_count_failure_by_reason(monkeypatch):
    """A failed heal() increments failed and records the reason."""
    stats = _fresh_stats(monkeypatch)
    storage = MagicMock()
    storage.load.return_value = None
    healer = healer_module.Healer(storage, 0.7)

    assert healer.heal('btn', 'key', '#submit', MagicMock()) is None

    assert stats.attempts == 1
    assert stats.healed == 0
    assert stats.failed == 1
    assert stats.failed_reasons == {'no-snapshot': 1}
    assert stats.avg_best_score is None


def test_stats_accumulate_across_heals(monkeypatch):
    """Multiple heals accumulate attempts/healed/failed."""
    stats = _fresh_stats(monkeypatch)
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.return_value = [_make_candidate()]
    driver.driver.find_elements.return_value = [MagicMock()]
    healer = healer_module.Healer(storage, 0.7)

    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        assert healer.heal('btn', 'key1', '#submit', driver) is not None

    # Same snapshot key but different element name — still a separate heal() call
    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        assert healer.heal('btn2', 'key2', '#submit', driver) is not None

    # A failing heal
    storage.load.return_value = None
    assert healer.heal('btn3', 'missing', '#submit', driver) is None

    assert stats.attempts == 3
    assert stats.healed == 2
    assert stats.failed == 1
    assert stats.failed_reasons == {'no-snapshot': 1}


def test_stats_avg_best_score_over_multiple_healed(monkeypatch):
    """avg_best_score averages best scores across all successful heals."""
    stats = _fresh_stats(monkeypatch)
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.driver.find_elements.return_value = [MagicMock()]
    healer = healer_module.Healer(storage, 0.0)  # accept any score

    # First heal: perfect match
    driver.execute_script.return_value = [_make_candidate()]
    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        healer.heal('btn', 'key1', '#submit', driver)

    # Second heal: partial match (same text, different id/parent) → lower but > 0 score
    driver.execute_script.return_value = [_make_candidate(attrs={'id': 'other'}, text='Click', parentTag='div')]
    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        healer.heal('btn2', 'key2', '#submit', driver)

    assert stats.healed == 2
    first_score = stats.avg_best_score * 2  # sum of both scores
    assert 0.0 < first_score < 2.0
