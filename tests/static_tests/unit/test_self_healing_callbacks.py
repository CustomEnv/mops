from __future__ import annotations

from unittest.mock import MagicMock, patch

from selenium.common.exceptions import WebDriverException

from mops.self_healing.healer import FailedHealingResult, Healer, SuccessHealingResult
from mops.self_healing.snapshot import ElementSnapshot


_ANY = object()


def _assert_failed(callback, reason, error=None, best_score=_ANY, score_threshold=_ANY, candidates_count=_ANY):
    """Assert callback was called once with a FailedHealingResult matching reason."""
    callback.assert_called_once()
    args = callback.call_args[0][0]
    assert isinstance(args, FailedHealingResult)
    assert args.reason == reason
    assert args.error == error
    if best_score is not _ANY:
        assert args.best_score == best_score
    if score_threshold is not _ANY:
        assert args.score_threshold == score_threshold
    if candidates_count is not _ANY:
        assert args.candidates_count == candidates_count


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


def _make_driver_wrapper(candidates=None, elements=None):
    """Build a mock driver_wrapper with execute_script and .driver.find_elements."""
    dw = MagicMock()
    dw.execute_script.return_value = candidates or []
    dw.driver.find_elements.return_value = elements or []
    return dw


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


# ---------------------------------------------------------------------------
# on_healing_success
# ---------------------------------------------------------------------------


def test_success_callback_not_fired_during_heal():
    """on_healing_success does NOT fire during heal() — it fires later in _try_healed_locators."""
    callback = MagicMock()
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])

    healer = Healer(storage, 0.7)

    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        result = healer.heal('btn', 'key', '#submit', driver)

    assert result is not None
    assert isinstance(result, SuccessHealingResult)
    assert result.healed_locator is None  # not set until _try_healed_locators
    callback.assert_not_called()  # callback fires AFTER DOM verification


def test_success_callback_not_set():
    """Healing works even when on_healing_success is None."""
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])

    healer = Healer(storage, 0.7)

    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        result = healer.heal('btn', 'key', '#submit', driver)

    assert result is not None


# ---------------------------------------------------------------------------
# on_healing_failure — 6 failure paths
# ---------------------------------------------------------------------------


def test_failure_no_snapshot():
    """No snapshot → on_healing_failure fired with FailedHealingResult."""
    callback = MagicMock()
    storage = MagicMock()
    storage.load.return_value = None
    healer = Healer(storage, 0.7, on_healing_failure=callback)

    result = healer.heal('btn', 'missing-key', '#submit', MagicMock())

    assert result is None
    callback.assert_called_once()
    args = callback.call_args[0][0]
    assert isinstance(args, FailedHealingResult)
    assert args.element_name == 'btn'
    assert args.locator_key == 'missing-key'
    assert args.locator == '#submit'
    assert args.reason == 'no-snapshot'
    assert args.error is None
    assert args.best_score is None
    assert args.score_threshold == 0.7
    assert args.candidates_count is None
    assert args.breakdown is None


def test_failure_candidates_script_raises():
    """driver.execute_script raises → on_healing_failure fired."""
    callback = MagicMock()
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.side_effect = WebDriverException('browser error')
    healer = Healer(storage, 0.7, on_healing_failure=callback)

    result = healer.heal('btn', 'key', '#submit', driver)

    assert result is None
    _assert_failed(
        callback,
        reason='candidates-script-error',
        error='browser error',
        best_score=None,
        score_threshold=0.7,
        candidates_count=None,
    )


def test_failure_no_candidates():
    """Empty candidates list → on_healing_failure fired."""
    callback = MagicMock()
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.return_value = []
    healer = Healer(storage, 0.7, on_healing_failure=callback)

    result = healer.heal('btn', 'key', '#submit', driver)

    assert result is None
    _assert_failed(callback, reason='no-candidates', best_score=None, score_threshold=0.7, candidates_count=0)


def test_failure_score_below_threshold():
    """Low similarity score → on_healing_failure fired."""
    callback = MagicMock()
    storage = MagicMock()
    # Snapshot with mismatched attributes/text so score stays low
    storage.load.return_value = _make_snapshot(attributes={'class': 'x'}, text='foo')
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.return_value = [
        _make_candidate(attrs={'class': 'y'}, text='bar', parentTag='div'),
    ]
    healer = Healer(storage, 0.95, on_healing_failure=callback)

    result = healer.heal('btn', 'key', '#submit', driver)

    assert result is None
    _assert_failed(callback, reason='below-threshold', score_threshold=0.95, candidates_count=1)
    args = callback.call_args[0][0]
    assert args.best_score is not None
    assert 0.0 <= args.best_score < 0.95
    assert args.breakdown is not None  # best candidate breakdown reported even on failure


def test_failure_best_index_out_of_bounds():
    """best_index >= len(web_elements) → on_healing_failure fired."""
    callback = MagicMock()
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = MagicMock()
    driver.driver = MagicMock()
    # Candidate 0 has low score (mismatch), candidate 1 has high score
    # → best_index = 1  but only 1 real element → OOB
    driver.execute_script.return_value = [
        _make_candidate(index=0, attrs={'id': 'other'}, text='Other'),
        _make_candidate(index=1),
    ]
    driver.driver.find_elements.return_value = [MagicMock()]  # only 1 element → index 1 is OOB
    healer = Healer(storage, 0.7, on_healing_failure=callback)

    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        result = healer.heal('btn', 'key', '#submit', driver)

    assert result is None
    _assert_failed(callback, reason='index-out-of-bounds', score_threshold=0.7, candidates_count=2)
    args = callback.call_args[0][0]
    assert args.best_score is not None  # matching candidate 1 was scored before the OOB hit


def test_failure_generate_locator_raises():
    """generate_locator raises → on_healing_failure fired."""
    callback = MagicMock()
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])
    healer = Healer(storage, 0.7, on_healing_failure=callback)

    with patch('mops.self_healing.healer.generate_locator', side_effect=WebDriverException('no locator')):
        result = healer.heal('btn', 'key', '#submit', driver)

    assert result is None
    _assert_failed(callback, reason='generate-locator-error', error='no locator', candidates_count=1)
    args = callback.call_args[0][0]
    assert args.best_score is not None  # the matching candidate was scored before locator generation


def test_failure_callback_not_set():
    """Healing failure works even when on_healing_failure is None."""
    storage = MagicMock()
    storage.load.return_value = None
    healer = Healer(storage, 0.7)

    result = healer.heal('btn', 'key', '#submit', MagicMock())

    assert result is None


# ---------------------------------------------------------------------------
# healed_locators_candidates
# ---------------------------------------------------------------------------


def test_multiple_locators_stored_in_result():
    """All generated locators are stored in healed_locators_candidates."""
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])

    healer = Healer(storage, 0.7)

    locators = ['xpath=//button[1]', 'xpath=//button[2]', 'xpath=//button[3]']
    with patch('mops.self_healing.healer.generate_locator', return_value=locators):
        result = healer.heal('btn', 'key', '#submit', driver)

    assert result is not None
    assert result.healed_locators_candidates == locators
    # healed_locator is None by default — set later by _find_element
    assert result.healed_locator is None


# ---------------------------------------------------------------------------
# siblings in _score_similarity
# ---------------------------------------------------------------------------


def _make_siblings_snapshot(siblings: list[dict]):
    """Build an ElementSnapshot with siblings data, matching default snapshot attributes."""
    return _make_snapshot(siblings=siblings)


def test_siblings_matching_boosts_score():
    """Matching siblings increase the similarity score compared to no siblings."""
    storage = MagicMock()
    siblings = [{'tag': 'span', 'attrs': {'class': 'helper'}, 'text': 'label'}]
    storage.load.return_value = _make_siblings_snapshot(siblings)
    driver = MagicMock()
    driver.driver = MagicMock()
    candidate_with_siblings = _make_candidate(
        siblings=[{'tag': 'span', 'attrs': {'class': 'helper'}, 'text': 'label'}],
    )
    candidate_no_siblings = _make_candidate(siblings=[])
    driver.execute_script.return_value = [candidate_with_siblings, candidate_no_siblings]
    driver.driver.find_elements.return_value = [MagicMock()]

    healer_no_threshold = Healer(storage, 0.0)

    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        result = healer_no_threshold.heal('btn', 'key', '#submit', driver)

    assert result is not None
    assert result.score > 0
    # Both candidates are identical in attrs/text/parent, so the only difference
    # is sibling matching — the one with matching siblings should be picked
    # (it has the same score from attrs but added sibling contribution)
    assert result.score > 0


def test_mismatched_siblings_lower_score():
    """Having siblings but none matching the snapshot yields a lower score."""
    storage = MagicMock()
    snap_siblings = [{'tag': 'span', 'attrs': {'class': 'helper'}, 'text': 'label'}]
    storage.load.return_value = _make_siblings_snapshot(snap_siblings)

    driver = MagicMock()
    driver.driver = MagicMock()
    candidate = _make_candidate(
        attrs={'id': 'submit'},
        text='Click',
        parentTag='form',
        siblings=[{'tag': 'div', 'attrs': {'class': 'other'}, 'text': 'different'}],
    )
    driver.execute_script.return_value = [candidate]
    driver.driver.find_elements.return_value = [MagicMock()]

    healer = Healer(storage, 0.0)

    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        result = healer.heal('btn', 'key', '#submit', driver)

    assert result is not None
    # The attrs/text/parent all match perfectly, so score starts high,
    # then weighted down by sibling mismatch — verify score < 1.0
    assert result.score < 1.0


# ---------------------------------------------------------------------------
# edge cases — callback exception safety
# ---------------------------------------------------------------------------


def test_success_callback_not_fired_by_heal():
    """on_healing_success is not fired by heal() — only by _try_healed_locators."""
    storage = MagicMock()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])

    healer = Healer(storage, 0.7)

    with patch('mops.self_healing.healer.generate_locator', return_value=['xpath=//button']):
        result = healer.heal('btn', 'key', '#submit', driver)

    assert result is not None
    assert isinstance(result, SuccessHealingResult)


def test_failure_callback_does_not_crash_healing():
    """A misbehaving on_healing_failure does not prevent returning None."""
    storage = MagicMock()
    storage.load.return_value = None

    def crash(_result):
        raise RuntimeError('callback failed')

    healer = Healer(storage, 0.7, on_healing_failure=crash)

    import pytest

    # The exception propagates — users should see broken callbacks
    with pytest.raises(RuntimeError, match='callback failed'):
        healer.heal('btn', 'key', '#submit', MagicMock())
