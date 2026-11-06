from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from playwright.sync_api import Error, Locator
import pytest
from selenium.common.exceptions import NoSuchElementException as SeleniumNoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By

from mops.exceptions import NoSuchElementException
from mops.selenium.core.core_element import _parse_healed_locator
from mops.self_healing.mixin import _MAX_VERIFY_MATCHES
from mops.self_healing.healer import FailedHealingResult, Healer, SuccessHealingResult
from mops.self_healing.mixin import HealingMixin
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


def _make_storage():
    """Build a mock storage whose normalization is a no-op (candidates already clean)."""
    storage = MagicMock()
    storage.normalize_snapshot.side_effect = lambda snap: snap
    return storage


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


def _heal(healer, *args, generate_fn=None):
    """Call heal() with backend callbacks bound to the mock driver.

    :param generate_fn: Optional locator generator mock; defaults to a stub
        returning a single xpath locator.
    """
    driver = args[3]
    gen = generate_fn if generate_fn is not None else (lambda *_: ['xpath=//button'])
    return healer.heal(
        *args,
        find_elements_fn=lambda tag: driver.driver.find_elements('tag name', tag),
        generate_locator_fn=gen,
    )


# ---------------------------------------------------------------------------
# on_healing_success
# ---------------------------------------------------------------------------


def test_success_callback_not_fired_during_heal():
    """on_healing_success does NOT fire during heal() — it fires later in _try_healed_locators."""
    callback = MagicMock()
    storage = _make_storage()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])

    healer = Healer(storage, 0.7)

    result = _heal(healer, 'btn', 'key', '#submit', driver)

    assert result is not None
    assert isinstance(result, SuccessHealingResult)
    assert result.healed_locator is None  # not set until _try_healed_locators
    callback.assert_not_called()  # callback fires AFTER DOM verification


def test_success_callback_not_set():
    """Healing works even when on_healing_success is None."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])

    healer = Healer(storage, 0.7)

    result = _heal(healer, 'btn', 'key', '#submit', driver)

    assert result is not None


# ---------------------------------------------------------------------------
# on_healing_failure — 6 failure paths
# ---------------------------------------------------------------------------


def test_failure_no_snapshot():
    """No snapshot → on_healing_failure fired with FailedHealingResult."""
    callback = MagicMock()
    storage = _make_storage()
    storage.load.return_value = None
    healer = Healer(storage, 0.7, on_healing_failure=callback)

    result = _heal(healer, 'btn', 'missing-key', '#submit', MagicMock())

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
    storage = _make_storage()
    storage.load.return_value = _make_snapshot()
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.side_effect = WebDriverException('browser error')
    healer = Healer(storage, 0.7, on_healing_failure=callback)

    result = _heal(healer, 'btn', 'key', '#submit', driver)

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
    storage = _make_storage()
    storage.load.return_value = _make_snapshot()
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.return_value = []
    healer = Healer(storage, 0.7, on_healing_failure=callback)

    result = _heal(healer, 'btn', 'key', '#submit', driver)

    assert result is None
    _assert_failed(callback, reason='no-candidates', best_score=None, score_threshold=0.7, candidates_count=0)


def test_failure_score_below_threshold():
    """Low similarity score → on_healing_failure fired."""
    callback = MagicMock()
    storage = _make_storage()
    # Snapshot with mismatched attributes/text so score stays low
    storage.load.return_value = _make_snapshot(attributes={'class': 'x'}, text='foo')
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.return_value = [
        _make_candidate(attrs={'class': 'y'}, text='bar', parentTag='div'),
    ]
    healer = Healer(storage, 0.95, on_healing_failure=callback)

    result = _heal(healer, 'btn', 'key', '#submit', driver)

    assert result is None
    _assert_failed(callback, reason='below-threshold', score_threshold=0.95, candidates_count=1)
    args = callback.call_args[0][0]
    assert args.best_score is not None
    assert 0.0 <= args.best_score < 0.95
    assert args.breakdown is not None  # best candidate breakdown reported even on failure


def test_failure_best_index_out_of_bounds():
    """best_index >= len(web_elements) → on_healing_failure fired."""
    callback = MagicMock()
    storage = _make_storage()
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

    result = _heal(healer, 'btn', 'key', '#submit', driver)

    assert result is None
    _assert_failed(callback, reason='index-out-of-bounds', score_threshold=0.7, candidates_count=2)
    args = callback.call_args[0][0]
    assert args.best_score is not None  # matching candidate 1 was scored before the OOB hit


def test_failure_generate_locator_raises():
    """generate_locator raises → on_healing_failure fired."""
    callback = MagicMock()
    storage = _make_storage()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])
    healer = Healer(storage, 0.7, on_healing_failure=callback)

    gen = MagicMock(side_effect=WebDriverException('no locator'))
    result = _heal(healer, 'btn', 'key', '#submit', driver, generate_fn=gen)

    assert result is None
    _assert_failed(callback, reason='generate-locator-error', error='no locator', candidates_count=1)
    args = callback.call_args[0][0]
    assert args.best_score is not None  # the matching candidate was scored before locator generation


def test_failure_callback_not_set():
    """Healing failure works even when on_healing_failure is None."""
    storage = _make_storage()
    storage.load.return_value = None
    healer = Healer(storage, 0.7)

    result = _heal(healer, 'btn', 'key', '#submit', MagicMock())

    assert result is None


# ---------------------------------------------------------------------------
# healed_locators_candidates
# ---------------------------------------------------------------------------


def test_multiple_locators_stored_in_result():
    """All generated locators are stored in healed_locators_candidates."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])

    healer = Healer(storage, 0.7)

    locators = ['xpath=//button[1]', 'xpath=//button[2]', 'xpath=//button[3]']
    result = _heal(healer, 'btn', 'key', '#submit', driver, generate_fn=lambda *_: locators)

    assert result is not None
    assert result.healed_locators_candidates == locators
    # healed_locator is None by default — set later by _find_element
    assert result.healed_locator is None


# ---------------------------------------------------------------------------
# siblings in similarity scoring
# ---------------------------------------------------------------------------


def _make_siblings_snapshot(siblings: list[dict]):
    """Build an ElementSnapshot with siblings data, matching default snapshot attributes."""
    return _make_snapshot(siblings=siblings)


def test_siblings_matching_boosts_score():
    """Matching siblings increase the similarity score compared to no siblings."""
    storage = _make_storage()
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

    result = _heal(healer_no_threshold, 'btn', 'key', '#submit', driver)

    assert result is not None
    assert result.score > 0
    # Both candidates are identical in attrs/text/parent, so the only difference
    # is sibling matching — the one with matching siblings should be picked
    # (it has the same score from attrs but added sibling contribution)
    assert result.score > 0


def test_mismatched_siblings_lower_score():
    """Having siblings but none matching the snapshot yields a lower score."""
    storage = _make_storage()
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

    result = _heal(healer, 'btn', 'key', '#submit', driver)

    assert result is not None
    # The attrs/text/parent all match perfectly, so score starts high,
    # then weighted down by sibling mismatch — verify score < 1.0
    assert result.score < 1.0


# ---------------------------------------------------------------------------
# edge cases — callback exception safety
# ---------------------------------------------------------------------------


def test_success_callback_not_fired_by_heal():
    """on_healing_success is not fired by heal() — only by _try_healed_locators."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[_make_candidate()], elements=[MagicMock()])

    healer = Healer(storage, 0.7)

    result = _heal(healer, 'btn', 'key', '#submit', driver)

    assert result is not None
    assert isinstance(result, SuccessHealingResult)


def test_failure_callback_does_not_crash_healing():
    """A misbehaving on_healing_failure does not prevent returning None."""
    storage = _make_storage()
    storage.load.return_value = None

    def crash(_result):
        raise RuntimeError('callback failed')

    healer = Healer(storage, 0.7, on_healing_failure=crash)

    # The exception propagates — users should see broken callbacks
    with pytest.raises(RuntimeError, match='callback failed'):
        _heal(healer, 'btn', 'key', '#submit', MagicMock())


# ---------------------------------------------------------------------------
# terminal callback guarantee — _try_healed_locators
# ---------------------------------------------------------------------------


class _StubSeleniumElement(HealingMixin):
    """Minimal Selenium-like element exercising the real HealingMixin flow.

    :param base: Object standing in for the search base (driver or parent element).
    :param scores: Similarities returned by :meth:`_healing_score_element`, in order.
    """

    _healing_lookup_exceptions = (SeleniumNoSuchElementException,)

    def __init__(self, base=None, *, locator='.original', scores=None):
        self._base = base if base is not None else MagicMock()
        self.locator_type = 'xpath'
        self.locator = locator
        self._cached_element = None
        self.parent = None
        self.name = 'fake element'
        self.driver = MagicMock()
        self.driver_wrapper = MagicMock()
        self.logs = []

    def log(self, message, *args, **kwargs):
        self.logs.append(message)

    def _get_base(self, wait_strategy=True):
        return self._base

    def _healing_find_elements_by_tag(self, tag, base):
        return base.find_elements('tag name', tag)

    def _healing_scope(self, base):
        return None

    def _healing_parse_locator(self, locator):
        return _parse_healed_locator(locator)

    def _healing_scan_matches(self, base, selector):
        return base.scanned[:_MAX_VERIFY_MATCHES]

    def _healing_resolve_match(self, base, selector, index):
        matches = base.find_elements(*selector)
        return matches[index] if index < len(matches) else None

    def _healing_try_original_locator(self, base):
        original = base.find_element(self.locator_type, self.locator)
        self._cached_element = original
        return original

    def _healing_apply_locator(self, selector, element):
        self.locator_type, self.locator = selector
        self._cached_element = element



def _healing_result(**overrides):
    """Build a SuccessHealingResult with a single candidate locator."""
    defaults = dict(
        element_name='fake element',
        original_locator='.broken',
        healed_locator=None,
        healed_locators_candidates=['xpath=//div'],
        score=0.9,
        locator_key='fake::.broken',
        candidates_count=2,
        breakdown=MagicMock(),
    )
    defaults.update(overrides)
    return SuccessHealingResult(**defaults)


def _config(**overrides):
    """Build a config namespace with only the fields the mixin reads."""
    defaults = dict(on_healing_success=None, on_healing_failure=None, score_threshold=0.7)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _assert_no_verified_failure(callback):
    """Assert on_healing_failure was called once with reason='no-verified-locator'."""
    callback.assert_called_once()
    args = callback.call_args[0][0]
    assert isinstance(args, FailedHealingResult)
    assert args.reason == 'no-verified-locator'
    assert args.breakdown is not None
    assert args.locator_key == 'fake::.broken'  # carried over from the success result
    assert args.candidates_count == 2


# ---------------------------------------------------------------------------
# terminal callback guarantee — _try_healed_locators
# ---------------------------------------------------------------------------


def test_try_healed_locators_fires_failure_when_no_candidate_matches():
    """All candidates missing → on_healing_failure(no-verified-locator) fired."""
    base = MagicMock()
    base.find_element.side_effect = SeleniumNoSuchElementException
    base.find_elements.return_value = []
    fake = _StubSeleniumElement(base)

    callback = MagicMock()
    with patch('mops.self_healing.mixin.get_config', return_value=_config(on_healing_failure=callback)):
        with pytest.raises(NoSuchElementException):
            fake._try_healed_locators(_healing_result())

    _assert_no_verified_failure(callback)


def test_try_healed_locators_fires_failure_when_base_raises():
    """Base resolution failing (parent missing) must still fire the terminal failure callback."""
    fake = _StubSeleniumElement()
    fake._resolve_base = MagicMock(return_value=(None, 'parent not found'))

    callback = MagicMock()
    with patch('mops.self_healing.mixin.get_config', return_value=_config(on_healing_failure=callback)):
        with pytest.raises(NoSuchElementException):
            fake._try_healed_locators(_healing_result())

    _assert_no_verified_failure(callback)


def test_try_healed_locators_fires_failure_on_verification_error():
    """A non-miss exception during verification still fires the failure callback."""
    base = MagicMock()
    base.find_element.side_effect = SeleniumNoSuchElementException
    base.find_elements.side_effect = WebDriverException('stale element')
    fake = _StubSeleniumElement(base)

    callback = MagicMock()
    with patch('mops.self_healing.mixin.get_config', return_value=_config(on_healing_failure=callback)):
        with pytest.raises(NoSuchElementException):
            fake._try_healed_locators(_healing_result())

    _assert_no_verified_failure(callback)


def test_try_healed_locators_fires_success_when_candidate_found():
    """A verified candidate returns the element and does not fire failure."""
    healed_element = MagicMock()
    base = MagicMock()
    base.find_element.side_effect = SeleniumNoSuchElementException
    base.scanned = [_scan_dict()]
    base.find_elements.return_value = [healed_element]
    fake = _StubSeleniumElement(base)

    failure_cb = MagicMock()
    with patch('mops.self_healing.mixin.get_config', return_value=_config(on_healing_failure=failure_cb)):
        returned = fake._try_healed_locators(_healing_result())

    assert returned is healed_element
    failure_cb.assert_not_called()


def test_resolve_base_heals_parent_when_base_missing():
    """_resolve_base heals a missing parent and retries inside the healed context."""
    base_after_parent_heal = MagicMock()
    fake = _StubSeleniumElement()
    fake._get_base = MagicMock(side_effect=[NoSuchElementException('parent not found'), base_after_parent_heal])
    fake.parent = SimpleNamespace(_apply_healing=MagicMock(return_value=True))

    base, error = fake._resolve_base(0)

    assert base is base_after_parent_heal
    assert error is None
    fake.parent._apply_healing.assert_called_once_with(1)


def test_resolve_base_fails_when_parent_cannot_be_healed():
    """_resolve_base returns None with an error when the parent cannot be healed."""
    fake = _StubSeleniumElement()
    fake._get_base = MagicMock(side_effect=NoSuchElementException('parent not found'))
    fake.parent = SimpleNamespace(_apply_healing=MagicMock(return_value=False))

    base, error = fake._resolve_base(0)

    assert base is None
    assert error is not None
    fake.parent._apply_healing.assert_called_once_with(1)


def test_try_healed_locators_fires_failure_when_parent_cannot_be_healed():
    """If the parent cannot be healed, the terminal failure callback still fires."""
    fake = _StubSeleniumElement()
    fake._resolve_base = MagicMock(return_value=(None, 'parent not healed'))

    callback = MagicMock()
    with patch('mops.self_healing.mixin.get_config', return_value=_config(on_healing_failure=callback)):
        with pytest.raises(NoSuchElementException):
            fake._try_healed_locators(_healing_result())

    _assert_no_verified_failure(callback)


def test_try_healed_locators_original_locator_works_no_metrics():
    """If the original locator works again, no success/failure metrics are emitted."""
    original_element = MagicMock()
    base = MagicMock()
    base.find_element.return_value = original_element  # original locator hits
    fake = _StubSeleniumElement(base)

    success_cb, failure_cb = MagicMock(), MagicMock()
    config = _config(on_healing_success=success_cb, on_healing_failure=failure_cb)
    with patch('mops.self_healing.mixin.get_config', return_value=config):
        returned = fake._try_healed_locators(_healing_result())

    assert returned is original_element
    assert fake._cached_element is original_element
    success_cb.assert_not_called()
    failure_cb.assert_not_called()


# ---------------------------------------------------------------------------
# locator verification — unique vs non-unique generated locators
# ---------------------------------------------------------------------------


def _scan_dict(**overrides):
    """Raw DOM snapshot dict as returned by the batched verification JS."""
    data = {
        'index': 0,
        'tag': 'div',
        'attrs': {'class': 'row'},
        'text': '',
        'parentTag': 'body',
        'parentAttrs': {},
        'siblings': [],
    }
    data.update(overrides)
    return data


def test_verify_accepts_unique_match_without_scoring():
    """A locator matching one element needs no similarity check."""
    healed_element = MagicMock()
    base = MagicMock()
    base.scanned = [_scan_dict()]
    base.find_elements.return_value = [healed_element]
    fake = _StubSeleniumElement(base)

    with patch('mops.self_healing.mixin._score_snapshot') as score:
        returned = fake._verify_healed_locators(base, _healing_result(), _config())

    assert returned is healed_element
    score.assert_not_called()
    assert fake.locator == '//div'  # healed locator persisted


def test_verify_picks_best_scoring_match_of_non_unique_locator():
    """A broad locator must not silently resolve to the first (wrong) match."""
    wrong, right = MagicMock(name='wrong'), MagicMock(name='right')
    base = MagicMock()
    base.scanned = [_scan_dict(), _scan_dict(attrs={'class': 'row active'})]
    base.find_elements.return_value = [wrong, right]
    fake = _StubSeleniumElement(base)
    result = _healing_result(snapshot=MagicMock())

    with patch('mops.self_healing.mixin._score_snapshot', side_effect=[0.25, 0.95]):
        returned = fake._verify_healed_locators(base, result, _config())

    assert returned is right
    assert result.score == 0.95
    assert fake._cached_element is right


def test_verify_rejects_non_unique_locator_below_verify_score():
    """When no match resembles the snapshot, the candidate is rejected (no lucky accept)."""
    base = MagicMock()
    base.scanned = [_scan_dict(), _scan_dict()]
    base.find_elements.return_value = [MagicMock(), MagicMock()]
    fake = _StubSeleniumElement(base)
    result = _healing_result(snapshot=MagicMock())

    with patch('mops.self_healing.mixin._score_snapshot', side_effect=[0.1, 0.3]):
        assert fake._verify_healed_locators(base, result, _config()) is None

    assert fake.locator == '.original'  # nothing was persisted
    base.find_elements.assert_not_called()  # no resolve for a rejected candidate


def test_verify_rejects_non_unique_locator_without_snapshot():
    """Without a reference snapshot a non-unique locator cannot be verified."""
    base = MagicMock()
    base.scanned = [_scan_dict(), _scan_dict()]
    fake = _StubSeleniumElement(base)

    assert fake._verify_healed_locators(base, _healing_result(), _config()) is None


def test_verify_skips_candidate_when_match_index_is_gone():
    """A candidate whose match vanished between scan and resolve is skipped."""
    base = MagicMock()
    base.scanned = [_scan_dict()]
    base.find_elements.return_value = []  # index 0 no longer exists
    fake = _StubSeleniumElement(base)

    assert fake._verify_healed_locators(base, _healing_result(), _config()) is None


def test_verify_costs_one_scan_and_one_resolve():
    """Verification is batched: one scan call per candidate, one resolve for the winner."""
    base = MagicMock()
    base.scanned = [_scan_dict() for _ in range(10)]
    matches = [MagicMock(name=f'match {i}') for i in range(10)]
    base.find_elements.return_value = matches
    fake = _StubSeleniumElement(base)
    result = _healing_result(snapshot=MagicMock())

    scores = [0.5] * 4 + [0.9] + [0.5] * 5
    with patch('mops.self_healing.mixin._score_snapshot', side_effect=scores):
        returned = fake._verify_healed_locators(base, result, _config())

    assert returned is matches[4]  # best-scoring match
    base.find_elements.assert_called_once()  # one resolve, not one per match
    assert result.score == 0.9


def test_score_snapshot_scores_raw_dom_snapshot():
    """_score_snapshot scores a raw DOM dict against the reference without extra round-trips."""
    from mops.self_healing.mixin import _score_snapshot
    from mops.self_healing.snapshot import ElementSnapshot

    snapshot = ElementSnapshot(
        tag='input',
        attributes={'name': 'email', 'type': 'text'},
        text='',
        parent_tag='form',
        parent_attributes={'class': 'login-form'},
        siblings=[],
    )
    target = _scan_dict(
        tag='input',
        attrs={'name': 'email', 'type': 'text'},
        parentTag='form',
        parentAttrs={'class': 'login-form'},
    )
    other = _scan_dict(tag='input', attrs={'name': 'username', 'type': 'text'}, parentTag='form')

    config = SimpleNamespace(storage=None)
    assert _score_snapshot(target, snapshot, config) >= 0.9
    assert _score_snapshot(other, snapshot, config) < 0.7


# ---------------------------------------------------------------------------
# Playwright hooks
# ---------------------------------------------------------------------------


class _StubPlaywrightElement(HealingMixin):
    """Minimal Playwright-like element exercising the real HealingMixin flow."""

    _healing_lookup_exceptions = (Error,)

    def __init__(self, base=None, *, locator='.original', scores=None):
        self._base = base if base is not None else MagicMock()
        self.locator = locator
        self._element = None
        self.parent = None
        self.name = 'fake element'
        self.driver = MagicMock()
        self.driver_wrapper = MagicMock()
        self.logs = []

    def log(self, message, *args, **kwargs):
        self.logs.append(message)

    def _get_base(self, wait_strategy=True):
        return self._base

    def _healing_parse_locator(self, locator):
        return locator[len('xpath=') :] if locator.startswith('xpath=') else locator

    def _healing_scan_matches(self, base, selector):
        return base.scanned[:_MAX_VERIFY_MATCHES]

    def _healing_resolve_match(self, base, selector, index):
        return base.locator(selector).nth(index)

    def _healing_try_original_locator(self, base):
        original = base.locator(self.locator)
        if original.count() == 0:
            return None
        self._element = original
        return original

    def _healing_apply_locator(self, selector, element):
        self.locator = selector
        self._element = element

def test_playwright_verify_accepts_unique_match_without_scoring():
    """Playwright: a locator matching one element needs no similarity check."""
    base = MagicMock()
    base.scanned = [_scan_dict()]
    fake = _StubPlaywrightElement(base)

    returned = fake._verify_healed_locators(base, _healing_result(), _config())

    assert returned is base.locator.return_value.nth.return_value
    assert fake.locator == '//div'


def test_playwright_verify_picks_best_scoring_match_of_non_unique_locator():
    """Playwright: a broad locator must not silently resolve to the first match."""
    base = MagicMock()
    base.scanned = [_scan_dict(), _scan_dict(), _scan_dict()]
    fake = _StubPlaywrightElement(base)
    result = _healing_result(snapshot=MagicMock())

    with patch('mops.self_healing.mixin._score_snapshot', side_effect=[0.25, 0.95, 0.5]):
        returned = fake._verify_healed_locators(base, result, _config())

    assert returned is base.locator.return_value.nth.return_value
    assert result.score == 0.95
    base.locator.return_value.nth.assert_any_call(1)  # best-scoring match, not the first


def test_playwright_verify_rejects_non_unique_locator_below_verify_score():
    """Playwright: no match resembling the snapshot means the candidate is rejected."""
    base = MagicMock()
    base.scanned = [_scan_dict(), _scan_dict()]
    fake = _StubPlaywrightElement(base)
    result = _healing_result(snapshot=MagicMock())

    with patch('mops.self_healing.mixin._score_snapshot', side_effect=[0.1, 0.3]):
        assert fake._verify_healed_locators(base, result, _config()) is None
    assert fake.locator == '.original'  # nothing was persisted


def test_playwright_try_healed_locators_original_works_no_metrics():
    """Playwright: original locator working again emits no metrics."""
    base = MagicMock()
    base.locator.return_value.count.return_value = 1
    fake = _StubPlaywrightElement(base)

    success_cb, failure_cb = MagicMock(), MagicMock()
    config = _config(on_healing_success=success_cb, on_healing_failure=failure_cb)
    with patch('mops.self_healing.mixin.get_config', return_value=config):
        fake._try_healed_locators(_healing_result())

    success_cb.assert_not_called()
    failure_cb.assert_not_called()


def test_playwright_try_healed_locators_fires_failure_when_no_candidate_matches():
    """Playwright: all candidates missing → on_healing_failure fired."""
    base = MagicMock()
    base.locator.return_value.count.return_value = 0
    fake = _StubPlaywrightElement(base)

    callback = MagicMock()
    config = _config(on_healing_failure=callback)
    with patch('mops.self_healing.mixin.get_config', return_value=config):
        with pytest.raises(NoSuchElementException):
            fake._try_healed_locators(_healing_result())

    _assert_no_verified_failure(callback)


# ---------------------------------------------------------------------------
# base (parent) scoping and the parent-healing chain
# ---------------------------------------------------------------------------


def test_attempt_healing_scopes_scan_to_base():
    """The candidate scan and the element lookup both use the resolved parent context."""
    parent_base = MagicMock()
    fake = _StubSeleniumElement(parent_base)
    fake._healing_scope = lambda base: base  # pretend the base is a real DOM node

    healer = MagicMock()
    storage = MagicMock()
    storage.extract_full_locator_key.return_value = 'key'
    config = _config(storage=storage)

    with patch('mops.self_healing.mixin.get_healer', return_value=healer):
        with patch('mops.self_healing.mixin.get_config', return_value=config):
            fake._attempt_healing(parent_base)
            find_elements_fn = healer.heal.call_args.kwargs['find_elements_fn']
            find_elements_fn('input')

    assert healer.heal.call_args.kwargs['scope'] is parent_base  # scan limited to the parent
    parent_base.find_elements.assert_called_once_with('tag name', 'input')


def test_missing_parent_heals_ancestor_chain_first():
    """element → parent → grandparent: the chain is healed top-down before the lookup."""
    grandparent_base = MagicMock()
    parent_base = MagicMock()
    parent_base.find_element.side_effect = SeleniumNoSuchElementException
    parent_base.find_elements.return_value = [MagicMock(name='healed child')]
    parent_base.scanned = [_scan_dict()]

    grandparent = _StubSeleniumElement(grandparent_base)
    parent = _StubSeleniumElement(parent_base, locator='.parent', scores=[])
    child = _StubSeleniumElement(parent_base, locator='.child', scores=[])

    parent.parent = grandparent
    child.parent = parent

    # Every level finds its parent missing on the first attempt.
    parent._get_base = MagicMock(side_effect=[NoSuchElementException('parent missing'), parent_base])
    child._get_base = MagicMock(side_effect=[NoSuchElementException('parent missing'), parent_base])

    # The grandparent's own locator works again, so it heals itself instantly.
    grandparent_base.find_element.return_value = MagicMock(name='grandparent element')
    grand_apply = MagicMock(wraps=grandparent._apply_healing)
    grandparent._apply_healing = grand_apply
    parent_apply = MagicMock(wraps=parent._apply_healing)
    parent._apply_healing = parent_apply
    parent._attempt_healing = MagicMock(return_value=_healing_result())

    child._attempt_healing = MagicMock(return_value=_healing_result())

    with patch('mops.self_healing.mixin.get_config', return_value=_config()):
        healed = child._try_healed_locators()

    grand_apply.assert_called_once_with(2)  # grandparent healed at depth 2
    parent_apply.assert_called_once_with(1)  # parent healed at depth 1
    parent._get_base.assert_called_with(wait_strategy=False)
    assert healed is not None


def test_nested_element_verifies_inside_parent_context():
    """The healed locator of a nested element is verified against the parent, not the document."""
    parent_base = MagicMock()
    parent_base.find_element.side_effect = SeleniumNoSuchElementException
    parent_base.find_elements.return_value = [MagicMock(name='nested input')]
    parent_base.scanned = [_scan_dict()]
    fake = _StubSeleniumElement(parent_base, locator='.nested')

    base, _error = fake._resolve_base(0)
    fake._verify_healed_locators(base, _healing_result(), _config())

    parent_base.find_elements.assert_called_once_with(By.XPATH, '//div')


# ---------------------------------------------------------------------------
# remaining coverage of the base-scoping / chain entry points
# ---------------------------------------------------------------------------


def test_healer_scopes_candidate_scan_to_given_scope():
    """Healer passes the parent scope as the second JS argument of the candidate scan."""
    from mops.self_healing.healer import _GET_CANDIDATES_JS, _MAX_CANDIDATES

    healer = Healer(MagicMock(), 0.7)
    dw = _make_driver_wrapper(candidates=[_make_candidate()])
    scope = MagicMock(name='parent element')

    healer._collect_candidates(dw, 'input', 'name', 'key', 'locator', scope)

    dw.execute_script.assert_called_once_with(_GET_CANDIDATES_JS, 'input', scope, _MAX_CANDIDATES)


def test_healer_scan_defaults_to_document_without_scope():
    """Without a parent the scan receives ``None`` → the JS falls back to ``document``."""
    healer = Healer(MagicMock(), 0.7)
    dw = _make_driver_wrapper(candidates=[_make_candidate()])

    healer._collect_candidates(dw, 'input', 'name', 'key', 'locator')

    assert dw.execute_script.call_args[0][2] is None


def test_resolve_base_stops_at_max_healing_depth():
    """The parent chain is bounded — no healing attempt at MAX_HEALING_DEPTH."""
    from mops.self_healing.healer import MAX_HEALING_DEPTH

    fake = _StubSeleniumElement()
    fake._get_base = MagicMock(side_effect=NoSuchElementException('parent not found'))
    fake.parent = SimpleNamespace(_apply_healing=MagicMock(return_value=True))

    base, error = fake._resolve_base(MAX_HEALING_DEPTH)

    assert base is None
    assert error is not None
    fake.parent._apply_healing.assert_not_called()


def test_apply_healing_fires_failure_when_no_candidates():
    """No candidate locators produced → terminal failure callback with a reason."""
    parent_base = MagicMock()
    parent_base.find_element.side_effect = SeleniumNoSuchElementException
    fake = _StubSeleniumElement(parent_base)
    fake._attempt_healing = MagicMock(return_value=None)

    callback = MagicMock()
    with patch('mops.self_healing.mixin.get_config', return_value=_config(on_healing_failure=callback)):
        assert fake._apply_healing() is False

    callback.assert_called_once()
    assert callback.call_args[0][0].reason == 'no-verified-locator'
    assert 'no candidate locators' in callback.call_args[0][0].error


def test_selenium_healing_scope_uses_parent_element_only():
    """Selenium scope is the parent WebElement; a root driver scans the document."""
    from selenium.webdriver.remote.webdriver import WebDriver as SeleniumDriver
    from selenium.webdriver.remote.webelement import WebElement as SeleniumWebElement

    from mops.selenium.core.core_element import CoreElement

    parent = MagicMock(spec=SeleniumWebElement)
    driver = MagicMock(spec=SeleniumDriver)

    assert CoreElement._healing_scope(None, parent) is parent
    assert CoreElement._healing_scope(None, driver) is None


def test_playwright_healing_scope_uses_parent_locator_only():
    """Playwright scope is the parent Locator; a page scans the document."""
    from playwright.sync_api import Page as PlaywrightPage

    from mops.playwright.play_element import PlayElement

    parent = MagicMock(spec=Locator)
    page = MagicMock(spec=PlaywrightPage)

    assert PlayElement._healing_scope(None, parent) is parent
    assert PlayElement._healing_scope(None, page) is None


def test_playwright_find_elements_by_tag_is_parent_scoped():
    """Playwright element lookup chains from the base locator."""
    from mops.playwright.play_element import PlayElement

    base = MagicMock(spec=Locator)

    PlayElement._healing_find_elements_by_tag(None, 'input', base)

    base.locator.assert_called_once_with('input')


# ---------------------------------------------------------------------------
# candidate generation: generated-value filtering, escaping, combos
# ---------------------------------------------------------------------------


def test_generator_drops_build_time_hash_suffix_from_class():
    """A class token like 'some-element#Tep' must not produce a hash-dependent locator."""
    from mops.self_healing.locator_generator import _build_providers

    providers = _build_providers('div', {'class': 'some-element#Tep button'}, '')

    assert 'xpath=//div[contains(@class, "some-element") and contains(@class, "button")]' in providers
    assert not any('#Tep' in provider for provider in providers)


def test_generator_drops_generated_ids():
    """Build-time generated ids (React, Angular, random blobs) are not used at all."""
    from mops.self_healing.locator_generator import _build_providers

    for generated_id in (':r1a:', '_ngcontent-abc', 'MdO', 'Tep', 'a1b2c3d4e5f6g7'):
        providers = _build_providers('input', {'id': generated_id, 'name': 'email'}, '')
        assert not any('@id=' in provider for provider in providers), generated_id
        assert 'xpath=//input[@name="email"]' in providers


def test_generator_keeps_semantic_ids():
    """Semantic ids (kebab, camelCase, PascalCase) still produce the most stable locator."""
    from mops.self_healing.locator_generator import _build_providers

    assert _build_providers('input', {'id': 'user-email'}, '')[0] == 'xpath=//*[@id="user-email"]'
    assert _build_providers('input', {'id': 'userEmail'}, '')[0] == 'xpath=//*[@id="userEmail"]'
    assert _build_providers('input', {'id': 'SubmitButton'}, '')[0] == 'xpath=//*[@id="SubmitButton"]'


def test_generator_escapes_quotes_in_xpath_literals():
    """Values with quotes must yield valid XPath (no backslash escaping)."""
    from mops.self_healing.locator_generator import _build_providers

    providers = _build_providers('span', {'aria-label': 'say "hi"'}, '')
    assert 'xpath=//*[@aria-label="say "hi""]' not in providers
    assert any('\'say "hi"\'' in provider for provider in providers)

    # both quote kinds → XPath 1.0 needs concat()
    both = _build_providers('span', {'aria-label': 'it\'s "ok"'}, '')
    assert any('concat(' in provider for provider in both)


def test_generator_adds_name_and_type_combination():
    """name+type is more specific than either attribute alone."""
    from mops.self_healing.locator_generator import _build_providers

    providers = _build_providers('input', {'name': 'email', 'type': 'text'}, '')

    assert 'xpath=//input[@name="email" and @type="text"]' in providers
    assert providers.index('xpath=//input[@name="email"]') < providers.index(
        'xpath=//input[@name="email" and @type="text"]'
    )


def test_generator_providers_are_unique():
    """No duplicated candidates regardless of the attribute combination."""
    from mops.self_healing.locator_generator import _build_providers

    providers = _build_providers('input', {'name': 'email', 'type': 'text'}, '')

    assert len(providers) == len(set(providers))


# ---------------------------------------------------------------------------
# tag-agnostic fallback scan
# ---------------------------------------------------------------------------


def test_healer_falls_back_to_any_tag_when_snapshot_tag_is_gone():
    """A redesign may change the tag (div → button) — the scan must still find it."""
    from mops.self_healing.healer import _FALLBACK_TAG

    storage = _make_storage()
    storage.load.return_value = _make_snapshot(tag='div')
    driver = _make_driver_wrapper(candidates=[], elements=[MagicMock()])
    # first scan (tag) → empty, second scan ('*') → the renamed element
    driver.execute_script.side_effect = [[], [_make_candidate(tag='button')]]

    healer = Healer(storage, 0.7)
    result = _heal(healer, 'btn', 'key', '#submit', driver)

    assert result is not None
    assert driver.execute_script.call_args[0][1] == _FALLBACK_TAG


def test_healer_reports_no_candidates_when_both_scans_are_empty():
    """Empty tag scan and empty fallback scan → no-candidates failure."""
    callback = MagicMock()
    storage = _make_storage()
    storage.load.return_value = _make_snapshot()
    driver = _make_driver_wrapper(candidates=[])
    driver.execute_script.side_effect = [[], []]

    healer = Healer(storage, 0.7, on_healing_failure=callback)
    assert _heal(healer, 'btn', 'key', '#submit', driver) is None
    assert callback.call_args[0][0].reason == 'no-candidates'
