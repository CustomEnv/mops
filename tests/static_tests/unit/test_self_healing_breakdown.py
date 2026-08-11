from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

from mops.self_healing.healer import AttributeMatch, Healer, SimilarityBreakdown
from mops.self_healing.snapshot import ElementSnapshot, JsonFileSnapshotStorage


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


def _make_storage():
    """Build a mock storage whose normalization is a no-op (candidates already clean)."""
    storage = MagicMock()
    storage.normalize_snapshot.side_effect = lambda snap: snap
    return storage


def _make_candidate(index: int = 0, **extra: str) -> dict:
    """Build a candidate dict with values matching the default snapshot."""
    return {
        'index': index,
        'attrs': {'id': 'submit'},
        'text': 'Click',
        'parentTag': 'form',
        'parentAttrs': {},
        'siblings': [],
        **extra,
    }


def _make_driver_wrapper(candidates=None, elements=None):
    """Build a mock driver_wrapper with execute_script and .driver.find_elements."""
    dw = MagicMock()
    dw.execute_script.return_value = candidates or []
    dw.driver.find_elements.return_value = elements or []
    return dw


def _heal(storage, driver, threshold: float = 0.7):
    """Run heal() with mocked backend callbacks and return the result."""
    healer = Healer(storage, threshold)
    return healer.heal(
        'btn', 'key', '#submit', driver,
        find_elements_fn=lambda tag: driver.driver.find_elements('tag name', tag),
        generate_locator_fn=lambda *_: ['xpath=//button'],
    )


# ---------------------------------------------------------------------------
# success result carries a breakdown
# ---------------------------------------------------------------------------


def test_success_result_has_breakdown():
    """A successful heal exposes a non-empty SimilarityBreakdown on the result."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])

    result = _heal(storage, driver)

    assert result is not None
    assert isinstance(result.breakdown, SimilarityBreakdown)
    assert result.breakdown.score == result.score
    assert 'id' in result.breakdown.attributes
    assert result.breakdown.attributes['id'].matched is True
    assert result.breakdown.attributes['id'].snapshot_value == 'submit'
    assert result.breakdown.attributes['id'].candidate_value == 'submit'
    assert result.breakdown.text_snapshot == 'Click'
    assert result.breakdown.text_candidate == 'Click'
    assert result.breakdown.text_score == 1.0
    assert result.breakdown.parent_tag_matched is True
    assert result.breakdown.parent_tag_snapshot == 'form'
    assert result.breakdown.parent_tag_candidate == 'form'
    assert result.breakdown.siblings_snapshot_count == 0
    assert result.breakdown.siblings_candidate_count == 0
    # the raw DOM snapshot of the best candidate is attached
    assert result.breakdown.candidate_snapshot is not None
    assert result.breakdown.candidate_snapshot.tag == 'button'
    assert result.breakdown.candidate_snapshot.attributes == {'id': 'submit'}
    assert result.breakdown.candidate_snapshot.text == 'Click'


# ---------------------------------------------------------------------------
# matched / mismatched split
# ---------------------------------------------------------------------------


def test_breakdown_splits_matched_and_mismatched_attributes():
    """matched_attributes and mismatched_attributes split correctly."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot(attributes={'id': 'submit', 'class': 'btn'})
    driver = _make_driver_wrapper(
        candidates=[_make_candidate(attrs={'id': 'submit', 'class': 'btn-other'})],
        elements=[MagicMock()],
    )

    result = _heal(storage, driver, threshold=0.0)

    assert result is not None
    breakdown = result.breakdown
    assert breakdown.matched_attributes == ['id']
    assert breakdown.mismatched_attributes == ['class']
    assert breakdown.attributes['class'].snapshot_value == 'btn'
    assert breakdown.attributes['class'].candidate_value == 'btn-other'
    assert breakdown.attributes['class'].matched is False


# ---------------------------------------------------------------------------
# dynamic data detection
# ---------------------------------------------------------------------------


def test_breakdown_detects_dynamic_attribute():
    """A changed dynamic id shows up as an unmatched attribute with both raw values."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot(attributes={'id': 'user-123'})
    driver = _make_driver_wrapper(
        candidates=[_make_candidate(attrs={'id': 'user-456'})],
        elements=[MagicMock()],
    )

    result = _heal(storage, driver, threshold=0.0)

    assert result is not None
    id_match = result.breakdown.attributes['id']
    assert isinstance(id_match, AttributeMatch)
    assert id_match.snapshot_value == 'user-123'
    assert id_match.candidate_value == 'user-456'
    assert id_match.matched is False
    assert id_match.score == 0.0
    assert 'id' in result.breakdown.mismatched_attributes


def test_breakdown_partial_token_overlap():
    """Class values with partial overlap produce a score strictly between 0 and 1."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot(attributes={'class': 'btn btn-primary'})
    driver = _make_driver_wrapper(
        candidates=[_make_candidate(attrs={'class': 'btn btn-secondary'})],
        elements=[MagicMock()],
    )

    result = _heal(storage, driver, threshold=0.0)

    assert result is not None
    class_match = result.breakdown.attributes['class']
    assert class_match.matched is False
    assert 0.0 < class_match.score < 1.0


def test_breakdown_snapshot_attribute_missing_on_candidate():
    """A snapshot attribute absent on the candidate is reported as unmatched."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot(attributes={'id': 'submit', 'name': 'go'})
    driver = _make_driver_wrapper(
        candidates=[_make_candidate(attrs={'id': 'submit'})],  # no 'name'
        elements=[MagicMock()],
    )

    result = _heal(storage, driver, threshold=0.0)

    assert result is not None
    name_match = result.breakdown.attributes['name']
    assert name_match.snapshot_value == 'go'
    assert name_match.candidate_value is None
    assert name_match.matched is False
    assert name_match.score == 0.0
    assert 'name' in result.breakdown.mismatched_attributes


def test_breakdown_includes_unweighted_snapshot_attributes():
    """Attributes outside ScoringWeights appear in the breakdown with weight 0.0."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot(attributes={'id': 'submit', 'data-testid': 'submit-btn'})
    driver = _make_driver_wrapper(
        candidates=[_make_candidate(attrs={'id': 'submit', 'data-testid': 'submit-btn'})],
        elements=[MagicMock()],
    )

    result = _heal(storage, driver, threshold=0.0)

    assert result is not None
    data_match = result.breakdown.attributes['data-testid']
    assert data_match.snapshot_value == 'submit-btn'
    assert data_match.matched is True
    assert data_match.weight == 0.0


# ---------------------------------------------------------------------------
# failure path — breakdown still reported
# ---------------------------------------------------------------------------


def test_below_threshold_failure_has_breakdown():
    """below-threshold failure still reports the best candidate's breakdown."""
    callback = MagicMock()
    storage = _make_storage()
    # Snapshot with mismatched attributes/text so score stays low
    storage.load.return_value = _make_snapshot(attributes={'id': 'user-123'}, text='foo')
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.return_value = [
        _make_candidate(attrs={'id': 'user-456'}, text='bar', parentTag='div'),
    ]
    healer = Healer(storage, 0.95, on_healing_failure=callback)

    result = healer.heal(
        'btn', 'key', '#submit', driver,
        find_elements_fn=lambda tag: driver.driver.find_elements('tag name', tag),
        generate_locator_fn=lambda *_: ['xpath=//button'],
    )

    assert result is None
    args = callback.call_args[0][0]
    assert args.reason == 'below-threshold'
    assert isinstance(args.breakdown, SimilarityBreakdown)
    assert args.breakdown.attributes['id'].snapshot_value == 'user-123'
    assert args.breakdown.attributes['id'].candidate_value == 'user-456'
    assert args.breakdown.attributes['id'].matched is False
    # even on failure the best candidate's raw snapshot is attached
    assert args.breakdown.candidate_snapshot is not None
    assert args.breakdown.candidate_snapshot.attributes['id'] == 'user-456'
    assert args.breakdown.candidate_snapshot.text == 'bar'


# ---------------------------------------------------------------------------
# candidate normalization — same rules as snapshots
# ---------------------------------------------------------------------------


def test_healing_normalizes_candidate_before_scoring(tmp_path):
    """A CSS-module hash in the candidate's class is cleaned before comparison."""
    storage = JsonFileSnapshotStorage(str(tmp_path))
    snapshot = _make_snapshot(attributes={'class': 'primary'})  # already-normalized reference
    driver = _make_driver_wrapper(
        candidates=[_make_candidate(attrs={'class': 'Button_1a2b3__xy primary'})],
        elements=[MagicMock()],
    )

    healer = Healer(storage, 0.7)
    with patch.object(storage, 'load', return_value=snapshot):
        result = healer.heal(
            'btn', 'key', '#submit', driver,
            find_elements_fn=lambda tag: driver.driver.find_elements('tag name', tag),
            generate_locator_fn=lambda *_: ['xpath=//button'],
        )

    assert result is not None
    class_match = result.breakdown.attributes['class']
    assert class_match.matched is True  # both sides normalized
    assert class_match.snapshot_value == 'primary'
    assert class_match.candidate_value == 'primary'
    # the raw candidate snapshot still reflects the actual DOM value
    assert result.breakdown.candidate_snapshot.attributes['class'] == 'Button_1a2b3__xy primary'


def test_healing_applies_custom_normalization_to_candidate(tmp_path):
    """Custom rules (e.g. numeric id suffixes) are applied to candidates too."""
    storage = JsonFileSnapshotStorage(str(tmp_path))
    storage.set_normalization_rules([*storage._normalization_rules, ('id', re.compile(r'-\d+'), '')])
    snapshot = _make_snapshot(attributes={'id': 'user'})
    driver = _make_driver_wrapper(
        candidates=[_make_candidate(attrs={'id': 'user-456'})],
        elements=[MagicMock()],
    )

    healer = Healer(storage, 0.7)
    with patch.object(storage, 'load', return_value=snapshot):
        result = healer.heal(
            'btn', 'key', '#submit', driver,
            find_elements_fn=lambda tag: driver.driver.find_elements('tag name', tag),
            generate_locator_fn=lambda *_: ['xpath=//button'],
        )

    assert result is not None
    id_match = result.breakdown.attributes['id']
    assert id_match.matched is True
    assert id_match.snapshot_value == 'user'
    assert id_match.candidate_value == 'user'
    assert result.breakdown.candidate_snapshot.attributes['id'] == 'user-456'
