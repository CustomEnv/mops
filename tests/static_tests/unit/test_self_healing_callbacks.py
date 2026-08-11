from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import NoSuchElementException as SeleniumNoSuchElementException
from selenium.common.exceptions import WebDriverException

from mops.exceptions import NoSuchElementException
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


def _selenium_element_stub(base=None, original_miss: bool = True):
    """Build a minimal object exposing the attrs _try_healed_locators touches.

    :param original_miss: When :obj:`True` (default), the original locator lookup
        raises ``NoSuchElement`` — so the healed-candidates path is exercised.
    """
    base = base or MagicMock()
    if original_miss:
        base.find_element.side_effect = SeleniumNoSuchElementException
    fake = SimpleNamespace(
        _get_base=MagicMock(return_value=base),
        _resolve_base=MagicMock(return_value=(base, None)),
        _verify_healed_locators=MagicMock(return_value=None),
        locator_type='xpath',
        locator='.original',
        _cached_element=None,
        parent=None,
        name='fake element',
        driver_wrapper=MagicMock(),
    )
    fake.log = lambda *a, **k: None
    return fake


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


def _assert_no_verified_failure(callback):
    """Assert on_healing_failure was called once with reason='no-verified-locator'."""
    callback.assert_called_once()
    args = callback.call_args[0][0]
    assert isinstance(args, FailedHealingResult)
    assert args.reason == 'no-verified-locator'
    assert args.breakdown is not None
    assert args.locator_key == 'fake::.broken'  # carried over from the success result
    assert args.candidates_count == 2


def test_try_healed_locators_fires_failure_when_no_candidate_matches():
    """All candidates missing → on_healing_failure(no-verified-locator) fired."""
    from mops.selenium.core.core_element import CoreElement

    fake = _selenium_element_stub()

    callback = MagicMock()
    config = SimpleNamespace(on_healing_success=None, on_healing_failure=callback, score_threshold=0.7)

    with patch('mops.selenium.core.core_element.get_config', return_value=config):
        with pytest.raises(NoSuchElementException):
            CoreElement._try_healed_locators(fake, _healing_result())

    _assert_no_verified_failure(callback)


def test_try_healed_locators_fires_failure_when_base_raises():
    """Base resolution failing (parent missing) must still fire the terminal failure callback."""
    from mops.selenium.core.core_element import CoreElement

    fake = _selenium_element_stub()
    fake._resolve_base.return_value = (None, 'parent not found')

    callback = MagicMock()
    config = SimpleNamespace(on_healing_success=None, on_healing_failure=callback, score_threshold=0.7)

    with patch('mops.selenium.core.core_element.get_config', return_value=config):
        with pytest.raises(NoSuchElementException):
            CoreElement._try_healed_locators(fake, _healing_result())

    _assert_no_verified_failure(callback)


def test_try_healed_locators_fires_failure_on_verification_error():
    """A non-miss exception during verification still fires the failure callback."""
    from mops.selenium.core.core_element import CoreElement

    fake = _selenium_element_stub()
    fake._verify_healed_locators.side_effect = WebDriverException('stale element')

    callback = MagicMock()
    config = SimpleNamespace(on_healing_success=None, on_healing_failure=callback, score_threshold=0.7)

    with patch('mops.selenium.core.core_element.get_config', return_value=config):
        with pytest.raises(NoSuchElementException):
            CoreElement._try_healed_locators(fake, _healing_result())

    _assert_no_verified_failure(callback)


def test_try_healed_locators_fires_success_when_candidate_found():
    """A verified candidate returns the element and does not fire failure."""
    from mops.selenium.core.core_element import CoreElement

    healed_element = MagicMock()
    fake = _selenium_element_stub()
    fake._verify_healed_locators.return_value = healed_element

    failure_cb = MagicMock()
    config = SimpleNamespace(on_healing_success=None, on_healing_failure=failure_cb, score_threshold=0.7)

    with patch('mops.selenium.core.core_element.get_config', return_value=config):
        returned = CoreElement._try_healed_locators(fake, _healing_result())

    assert returned is healed_element
    failure_cb.assert_not_called()


def test_resolve_base_heals_parent_when_base_missing():
    """_resolve_base heals a missing parent and retries inside the healed context."""
    from mops.selenium.core.core_element import CoreElement

    base_after_parent_heal = MagicMock()
    fake = _selenium_element_stub()
    fake._get_base.side_effect = [NoSuchElementException('parent not found'), base_after_parent_heal]
    fake.parent = SimpleNamespace(_apply_healing=MagicMock(return_value=True))

    base, error = CoreElement._resolve_base(fake, 0)

    assert base is base_after_parent_heal
    assert error is None
    fake.parent._apply_healing.assert_called_once_with(1)


def test_resolve_base_fails_when_parent_cannot_be_healed():
    """_resolve_base returns None with an error when the parent cannot be healed."""
    from mops.selenium.core.core_element import CoreElement

    fake = _selenium_element_stub()
    fake._get_base.side_effect = NoSuchElementException('parent not found')
    fake.parent = SimpleNamespace(_apply_healing=MagicMock(return_value=False))

    base, error = CoreElement._resolve_base(fake, 0)

    assert base is None
    assert error is not None
    fake.parent._apply_healing.assert_called_once_with(1)


def test_try_healed_locators_fires_failure_when_parent_cannot_be_healed():
    """If the parent cannot be healed, the terminal failure callback still fires."""
    from mops.selenium.core.core_element import CoreElement

    fake = _selenium_element_stub()
    fake._resolve_base.return_value = (None, 'parent not healed')

    callback = MagicMock()
    config = SimpleNamespace(on_healing_success=None, on_healing_failure=callback, score_threshold=0.7)

    with patch('mops.selenium.core.core_element.get_config', return_value=config):
        with pytest.raises(NoSuchElementException):
            CoreElement._try_healed_locators(fake, _healing_result())

    _assert_no_verified_failure(callback)


def test_verify_healed_locators_fires_success_and_persists_locator():
    """_verify_healed_locators persists the first hit and fires on_healing_success."""
    from mops.selenium.core.core_element import CoreElement

    healed_element = MagicMock()
    base = MagicMock()
    base.find_element.return_value = healed_element
    fake = _selenium_element_stub(base=base, original_miss=False)
    result = _healing_result()

    success_cb = MagicMock()
    config = SimpleNamespace(on_healing_success=success_cb, on_healing_failure=None, score_threshold=0.7)

    returned = CoreElement._verify_healed_locators(fake, base, result, config)

    assert returned is healed_element
    success_cb.assert_called_once_with(result)
    assert fake.locator == '//div'  # healed locator persisted
    assert result.healed_locator == 'xpath=//div'


def test_try_healed_locators_original_locator_works_no_metrics():
    """If the original locator works again, no success/failure metrics are emitted."""
    from mops.selenium.core.core_element import CoreElement

    original_element = MagicMock()
    base = MagicMock()
    base.find_element.return_value = original_element  # original locator hits
    fake = _selenium_element_stub(base=base, original_miss=False)

    success_cb = MagicMock()
    failure_cb = MagicMock()
    config = SimpleNamespace(on_healing_success=success_cb, on_healing_failure=failure_cb, score_threshold=0.7)

    with patch('mops.selenium.core.core_element.get_config', return_value=config):
        returned = CoreElement._try_healed_locators(fake, _healing_result())

    assert returned is original_element
    assert fake._cached_element is original_element
    success_cb.assert_not_called()
    failure_cb.assert_not_called()


def test_playwright_try_healed_locators_original_works_no_metrics():
    """Playwright: original locator working again emits no metrics."""
    from mops.playwright.play_element import PlayElement

    base = MagicMock()
    fake = SimpleNamespace(
        _get_base=MagicMock(return_value=base),
        _resolve_base=MagicMock(return_value=(base, None)),
        _verify_healed_locators=MagicMock(return_value=None),
        _parse_healed_locator_pw=MagicMock(side_effect=lambda s: s[len('xpath='):]),
        locator='.original',
        _element=None,
        parent=None,
        name='fake element',
        driver_wrapper=MagicMock(),
    )
    fake.log = lambda *a, **k: None
    # original locator hits: count() > 0
    fake._get_base.return_value.locator.return_value.count.return_value = 1

    success_cb = MagicMock()
    failure_cb = MagicMock()
    config = SimpleNamespace(on_healing_success=success_cb, on_healing_failure=failure_cb, score_threshold=0.7)

    with patch('mops.playwright.play_element.get_config', return_value=config):
        PlayElement._try_healed_locators(fake, _healing_result())

    success_cb.assert_not_called()
    failure_cb.assert_not_called()


def test_playwright_try_healed_locators_fires_failure_when_no_candidate_matches():
    """Playwright: all candidates missing → on_healing_failure fired."""
    from mops.playwright.play_element import PlayElement

    base = MagicMock()
    fake = SimpleNamespace(
        _get_base=MagicMock(return_value=base),
        _resolve_base=MagicMock(return_value=(base, None)),
        _verify_healed_locators=MagicMock(return_value=None),
        _parse_healed_locator_pw=MagicMock(side_effect=lambda s: s[len('xpath='):]),
        locator='.original',
        _element=None,
        parent=None,
        name='fake element',
        driver_wrapper=MagicMock(),
    )
    fake.log = lambda *a, **k: None
    # original locator miss by default: count() == 0
    fake._get_base.return_value.locator.return_value.count.return_value = 0

    callback = MagicMock()
    config = SimpleNamespace(on_healing_success=None, on_healing_failure=callback, score_threshold=0.7)

    with patch('mops.playwright.play_element.get_config', return_value=config):
        with pytest.raises(NoSuchElementException):
            PlayElement._try_healed_locators(fake, _healing_result())

    _assert_no_verified_failure(callback)
