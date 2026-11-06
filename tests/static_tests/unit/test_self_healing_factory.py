from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

import mops.self_healing.healer_factory as factory_module
from mops.self_healing import configure
from mops.self_healing.healer import Healer, ScoringWeights
from mops.self_healing.healer_factory import _HealerState, get_healer
from mops.self_healing.snapshot import JsonFileSnapshotStorage


@pytest.fixture(autouse=True)
def _cleanup_config():
    yield
    configure(
        save_snapshots=False,
        heal_locators=False,
        score_threshold=0.7,
        storage=None,
        scoring_weights=None,
        on_healing_success=None,
        on_healing_failure=None,
    )


def _fresh_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset the module-level healer singleton state."""
    monkeypatch.setattr(_HealerState, 'storage', None)
    monkeypatch.setattr(_HealerState, 'score_threshold', None)
    monkeypatch.setattr(_HealerState, 'scoring_weights', None)
    monkeypatch.setattr(_HealerState, 'on_healing_failure', None)
    monkeypatch.setattr(_HealerState, 'healer', None)


def _base_config(tmp_path) -> JsonFileSnapshotStorage:
    storage = JsonFileSnapshotStorage(str(tmp_path))
    configure(storage=storage, score_threshold=0.7, scoring_weights=ScoringWeights())
    return storage


def test_get_healer_reuses_instance_when_config_unchanged(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _fresh_state(monkeypatch)
    _base_config(tmp_path)

    first = get_healer()
    second = get_healer()

    assert isinstance(first, Healer)
    assert first is second


def test_get_healer_recreates_on_new_scoring_weights(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _fresh_state(monkeypatch)
    _base_config(tmp_path)

    before = get_healer()

    configure(scoring_weights=ScoringWeights(attribute={'class': 1.0}))
    after = get_healer()

    assert before is not after
    assert after._scoring_weights.attribute == {'class': 1.0}


def test_get_healer_recreates_on_new_threshold(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _fresh_state(monkeypatch)
    _base_config(tmp_path)

    before = get_healer()

    configure(score_threshold=0.95)
    after = get_healer()

    assert before is not after
    assert after._score_threshold == 0.95


def test_get_healer_recreates_on_new_failure_callback(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _fresh_state(monkeypatch)
    _base_config(tmp_path)

    before = get_healer()

    callback = MagicMock()
    configure(on_healing_failure=callback)
    after = get_healer()

    assert before is not after
    assert after._on_healing_failure is callback


def test_get_healer_recreates_on_new_storage(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _fresh_state(monkeypatch)
    _base_config(tmp_path)

    before = get_healer()

    other_storage = JsonFileSnapshotStorage(str(tmp_path / 'other'))
    configure(storage=other_storage)
    after = get_healer()

    assert before is not after
    assert after._storage is other_storage


def test_get_healer_reflects_in_place_weight_mutation(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Mutating the same ScoringWeights object is visible to the Healer immediately."""
    _fresh_state(monkeypatch)
    storage = JsonFileSnapshotStorage(str(tmp_path))
    weights = ScoringWeights(attribute={'id': 1.0})
    configure(storage=storage, score_threshold=0.7, scoring_weights=weights)

    healer = get_healer()

    weights.attribute['class'] = 0.5  # mutate the object in place

    assert healer._scoring_weights is weights
    assert healer._scoring_weights.attribute['class'] == 0.5


def test_get_healer_returns_none_storage_healer(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_healer() with no configured storage creates a Healer with None storage."""
    _fresh_state(monkeypatch)
    configure(save_snapshots=True, heal_locators=True)

    healer = get_healer()

    assert healer._storage is None
