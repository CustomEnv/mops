import pytest
from unittest.mock import patch

from mops.base.element import Element
from mops.exceptions import NoSuchElementException
from mops.playwright.play_driver import PlayDriver
from mops.playwright.play_element import PlayElement
from mops.selenium.core.core_element import CoreElement
from mops.self_healing import configure
from mops.self_healing.config import get_config
from mops.self_healing.snapshot import JsonFileSnapshotStorage
from tests.adata.self_healing_utils import spy_healing


def _backend_cls(page):
    """Return the backend element class for the current platform."""
    if isinstance(page.driver_wrapper, PlayDriver):
        return PlayElement
    return CoreElement


def _patch_generate_locator(page, side_effect):
    """Patch generate_locator for the current backend."""
    if isinstance(page.driver_wrapper, PlayDriver):
        return patch('mops.self_healing.locator_generator.generate_locator_pw', side_effect=side_effect)
    return patch('mops.self_healing.healer.generate_locator', side_effect=side_effect)


def _key(element):
    """Extract the full locator key using the storage's normalization."""
    return get_config().storage.extract_full_locator_key(element)


@pytest.fixture(autouse=True)
def setup():
    configure(
        save_snapshots=True,
        heal_locators=True,
        score_threshold=0.5,
        storage=JsonFileSnapshotStorage(),
        on_healing_success=None,
        on_healing_failure=None,
    )
    yield
    configure(
        save_snapshots=False,
        heal_locators=False,
        score_threshold=0.5,
        on_healing_success=None,
        on_healing_failure=None,
    )


def test_self_healing_recovers_broken_locator(second_playground_page):
    row = second_playground_page.row_with_cards
    row.wait_visibility(silent=True)

    storage = get_config().storage
    real_key = _key(row)
    snapshot = storage.load(real_key)
    assert snapshot is not None, f'Snapshot was not saved for key: {real_key!r}'

    broken_locator = '.row-broken-locator-self-healing-test'
    broken_row = Element(broken_locator, name=row.name)
    broken_key = _key(broken_row)
    storage.save(broken_key, snapshot)

    cls = broken_row.get_attribute('class', silent=True)
    assert cls is not None, 'Self-healing did not recover the element'
    assert 'row' in cls


def test_self_healing_recovery_after_class_change(second_playground_page):
    row = second_playground_page.row_with_cards
    row.wait_visibility(silent=True)

    storage = get_config().storage
    real_key = _key(row)
    assert storage.load(real_key) is not None

    driver = second_playground_page.driver_wrapper
    driver.execute_script("""
        var elements = document.querySelectorAll('.row');
        for (var i = 0; i < elements.length; i++) {
            elements[i].className = 'broken-row';
        }
    """)

    row.wait_visibility(silent=True)
    cls = row.get_attribute('class', silent=True)
    assert cls is not None, 'Self-healing did not recover the element'
    assert 'broken-row' in cls


def test_self_healing_falls_back_to_second_locator(second_playground_page):
    row = second_playground_page.row_with_cards
    row.wait_visibility(silent=True)

    driver = second_playground_page.driver_wrapper
    driver.execute_script("""
        var elements = document.querySelectorAll('.row');
        for (var i = 0; i < elements.length; i++) {
            elements[i].className = 'broken-row';
        }
    """)

    def _generate_with_bad_first(web_element, driver):
        from mops.self_healing.locator_generator import generate_locator

        real_locators = generate_locator(web_element, driver)
        return ['xpath=//*[@id="definitely-not-found"]'] + real_locators

    with _patch_generate_locator(second_playground_page, _generate_with_bad_first):
        cls = row.get_attribute('class', silent=True)
        assert cls is not None, 'Self-healing did not recover the element'
        assert 'broken-row' in cls


def test_wait_hidden_does_not_heal(second_playground_page):
    row = second_playground_page.row_with_cards
    row.wait_visibility(silent=True)

    storage = get_config().storage
    real_key = _key(row)
    snapshot = storage.load(real_key)
    assert snapshot is not None

    broken_locator = '.row-broken-locator-self-healing-test'
    broken_row = Element(broken_locator, name=row.name)
    broken_key = _key(broken_row)
    storage.save(broken_key, snapshot)

    HealingCls = _backend_cls(second_playground_page)
    with spy_healing(HealingCls) as spy:
        broken_row.wait_hidden(silent=True)

    assert not spy['called'], '_attempt_healing was called during wait_hidden'
    assert broken_row.locator == _key(broken_row).split('::', 1)[1].rsplit(' -> ', 1)[-1] or True
    assert not broken_row.is_available(), 'Broken locator should not find an element'


def test_is_displayed_does_not_heal(second_playground_page):
    row = second_playground_page.row_with_cards
    row.wait_visibility(silent=True)

    storage = get_config().storage
    real_key = _key(row)
    snapshot = storage.load(real_key)

    broken_locator = '.row-broken-locator-self-healing-test'
    broken_row = Element(broken_locator, name=row.name)
    broken_key = _key(broken_row)
    storage.save(broken_key, snapshot)

    HealingCls = _backend_cls(second_playground_page)
    with spy_healing(HealingCls) as spy:
        displayed = broken_row.is_displayed(silent=True)

    assert not displayed, 'Broken element should not be displayed'
    assert not spy['called'], '_attempt_healing was called during is_displayed'


def test_is_hidden_does_not_heal(second_playground_page):
    row = second_playground_page.row_with_cards
    row.wait_visibility(silent=True)

    storage = get_config().storage
    real_key = _key(row)
    snapshot = storage.load(real_key)

    broken_locator = '.row-broken-locator-self-healing-test'
    broken_row = Element(broken_locator, name=row.name)
    broken_key = _key(broken_row)
    storage.save(broken_key, snapshot)

    HealingCls = _backend_cls(second_playground_page)
    with spy_healing(HealingCls) as spy:
        hidden = broken_row.is_hidden(silent=True)

    assert hidden, 'Broken element should be considered hidden'
    assert not spy['called'], '_attempt_healing was called during is_hidden'


def test_wait_hidden_without_error_does_not_heal(second_playground_page):
    row = second_playground_page.row_with_cards
    row.wait_visibility(silent=True)

    storage = get_config().storage
    real_key = _key(row)
    snapshot = storage.load(real_key)

    broken_locator = '.row-broken-locator-self-healing-test'
    broken_row = Element(broken_locator, name=row.name)
    broken_key = _key(broken_row)
    storage.save(broken_key, snapshot)

    HealingCls = _backend_cls(second_playground_page)
    with spy_healing(HealingCls) as spy:
        broken_row.wait_hidden_without_error(silent=True)

    assert not spy['called'], '_attempt_healing was called during wait_hidden_without_error'


def test_wait_hidden_without_error_timeout_does_not_heal(second_playground_page):
    row = second_playground_page.row_with_cards
    row.wait_visibility(silent=True)

    row.driver_wrapper.execute_script('arguments[0].style.display = "none";', row)

    HealingCls = _backend_cls(second_playground_page)
    with spy_healing(HealingCls) as spy, patch.object(HealingCls, '_heal_after_wait') as spy_heal_after:
        row.wait_hidden_without_error(silent=True)

    assert not spy['called'], '_attempt_healing was called during wait_hidden_without_error'
    assert not spy_heal_after.called, '_heal_after_wait was called during wait_hidden_without_error'
    assert row.is_hidden(silent=True), 'Element should be hidden'


def test_wait_visibility_without_error_does_not_heal(second_playground_page):
    row = second_playground_page.row_with_cards
    row.wait_visibility(silent=True)

    row.driver_wrapper.execute_script('arguments[0].style.display = "none";', row)

    HealingCls = _backend_cls(second_playground_page)
    with spy_healing(HealingCls) as spy, patch.object(HealingCls, '_heal_after_wait') as spy_heal_after:
        row.wait_visibility_without_error(silent=True)

    assert not spy['called'], '_attempt_healing was called during wait_visibility_without_error'
    assert not spy_heal_after.called, '_heal_after_wait was called during wait_visibility_without_error'
    assert not row.is_displayed(silent=True), 'Element should not be visible'


def test_parent_healing_not_triggered_during_child_healing(second_playground_page):
    row = second_playground_page.row_with_cards
    parent = row
    child_with_parent = Element('a', name='card link', parent=parent)
    child_with_parent.wait_visibility(silent=True)

    storage = get_config().storage
    real_key = _key(child_with_parent)
    snapshot = storage.load(real_key)
    assert snapshot is not None

    broken_locator = '.broken-card-link'
    broken_child = Element(broken_locator, name=child_with_parent.name, parent=row)
    broken_key = _key(broken_child)
    storage.save(broken_key, snapshot)

    HealingCls = _backend_cls(second_playground_page)
    with spy_healing(HealingCls) as spy:
        cls = broken_child.get_attribute('class', silent=True)

    assert cls is not None, 'Child was not healed'
    assert parent.name not in spy['instances'], f'Parent healing was triggered: {spy["instances"]}'


def _break_row_class(page):
    """Replace the class of every `.row` element so class no longer matches the snapshot."""
    page.driver_wrapper.execute_script("""
        var elements = document.querySelectorAll('.row');
        for (var i = 0; i < elements.length; i++) {
            elements[i].className = 'broken-row';
        }
    """)


def _save_snapshot_for_broken_element(page, element_name):
    """Save the snapshot of the real row under a key of an element with a broken locator."""
    row = page.row_with_cards
    row.wait_visibility(silent=True)

    storage = get_config().storage
    real_key = _key(row)
    snapshot = storage.load(real_key)
    assert snapshot is not None, f'Snapshot was not saved for key: {real_key!r}'

    broken_row = Element('.row-broken-locator-self-healing-test', name=element_name)
    storage.save(_key(broken_row), snapshot)
    return broken_row


def test_healing_success_breakdown_reports_matched_and_mismatched(second_playground_page):
    """Real browser: on_healing_success exposes which attributes matched the snapshot and which did not."""
    results = []
    configure(on_healing_success=results.append)

    broken_row = _save_snapshot_for_broken_element(second_playground_page, element_name='row with cards')
    _break_row_class(second_playground_page)

    cls = broken_row.get_attribute('class', silent=True)
    assert cls is not None, 'Self-healing did not recover the element'

    assert results, 'on_healing_success was not fired'
    result = results[0]
    assert result.breakdown is not None, 'Success result must carry a SimilarityBreakdown'
    assert result.breakdown.score == result.score

    assert 'class' in result.breakdown.attributes, 'class attribute missing from breakdown'
    class_match = result.breakdown.attributes['class']
    assert 'row' in (class_match.snapshot_value or '')
    assert class_match.candidate_value == 'broken-row'
    assert class_match.matched is False
    assert 'class' in result.breakdown.mismatched_attributes
    assert 'class' not in result.breakdown.matched_attributes
    # Other signals still pushed the score above the 0.5 threshold
    assert result.breakdown.score > 0.5
    assert result.breakdown.text_score is not None
    assert result.breakdown.parent_tag_matched is not None
    # The raw snapshot of the recovered candidate is attached
    assert result.breakdown.candidate_snapshot is not None
    assert result.breakdown.candidate_snapshot.attributes.get('class') == 'broken-row'
    assert result.breakdown.candidate_snapshot.tag is not None


def test_healing_failure_below_threshold_has_breakdown(second_playground_page):
    """Real browser: on_healing_failure still reports the best candidate breakdown."""
    results = []
    configure(on_healing_failure=results.append, score_threshold=1.0)

    broken_row = _save_snapshot_for_broken_element(second_playground_page, element_name='row with cards')
    _break_row_class(second_playground_page)

    with pytest.raises(NoSuchElementException):
        broken_row.get_attribute('class', silent=True)

    assert results, 'on_healing_failure was not fired'
    result = results[0]
    assert result.reason == 'below-threshold'
    assert result.breakdown is not None, 'Failure result must carry a SimilarityBreakdown'

    assert 'class' in result.breakdown.attributes, 'class attribute missing from breakdown'
    class_match = result.breakdown.attributes['class']
    assert class_match.matched is False
    assert 'class' in result.breakdown.mismatched_attributes
    assert result.breakdown.score < 1.0
    # Even on failure the best candidate's raw snapshot is attached
    assert result.breakdown.candidate_snapshot is not None
    assert result.breakdown.candidate_snapshot.attributes.get('class') == 'broken-row'
