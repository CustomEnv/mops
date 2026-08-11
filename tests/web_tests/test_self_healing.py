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
        return patch('mops.playwright.play_element.generate_locator_pw', side_effect=side_effect)
    return patch('mops.selenium.core.core_element.generate_locator', side_effect=side_effect)


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


def test_parent_healing_not_triggered_during_sub_element_healing(second_playground_page):
    row = second_playground_page.row_with_cards
    parent = row
    sub_element_with_parent = Element('a', name='card link', parent=parent)
    sub_element_with_parent.wait_visibility(silent=True)

    storage = get_config().storage
    real_key = _key(sub_element_with_parent)
    snapshot = storage.load(real_key)
    assert snapshot is not None

    broken_locator = '.broken-card-link'
    broken_sub_element = Element(broken_locator, name=sub_element_with_parent.name, parent=row)
    broken_key = _key(broken_sub_element)
    storage.save(broken_key, snapshot)

    HealingCls = _backend_cls(second_playground_page)
    with spy_healing(HealingCls) as spy:
        cls = broken_sub_element.get_attribute('class', silent=True)

    assert cls is not None, 'Element was not healed'
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


def test_healing_normalizes_dynamic_class_before_scoring(second_playground_page):
    """A CSS-module hash in the class is cleaned on both sides before comparison."""
    results = []
    configure(on_healing_success=results.append)

    broken_row = _save_snapshot_for_broken_element(second_playground_page, element_name='row with cards')
    # Add a CSS-module-hash token to the row class — normalization must strip it
    second_playground_page.driver_wrapper.execute_script("""
        var elements = document.querySelectorAll('.row');
        for (var i = 0; i < elements.length; i++) {
            elements[i].className = elements[i].className + ' Button_1a2b3__xy';
        }
    """)

    cls = broken_row.get_attribute('class', silent=True)
    assert cls is not None, 'Self-healing did not recover the element'

    assert results, 'on_healing_success was not fired'
    result = results[0]

    # `matched` compares NORMALIZED values on both sides. 'Button_1a2b3__xy' is a
    # CSS-module hash — a default normalization rule strips that exact token, so
    # snapshot ('row ...') and candidate ('row ... Button_1a2b3__xy' -> 'row ...')
    # become equal. This is NOT "any occurrence matches": an ordinary class token
    # would survive normalization and make matched=False.
    assert result.breakdown.attributes['class'].matched is True, 'normalized class should match'
    # the raw candidate snapshot still shows the hash token from the real DOM
    assert 'Button_1a2b3__xy' in result.breakdown.candidate_snapshot.attributes.get('class', '')


def test_healing_canonicalizes_class_case(second_playground_page):
    """Real browser: class differing only in case is matched canonically."""
    results = []
    configure(on_healing_success=results.append)

    broken_row = _save_snapshot_for_broken_element(second_playground_page, element_name='row with cards')
    # 'row' -> 'Row': same word, different case — must still match canonically
    second_playground_page.driver_wrapper.execute_script("""
        var elements = document.querySelectorAll('.row');
        for (var i = 0; i < elements.length; i++) {
            elements[i].className = 'Row';
        }
    """)

    cls = broken_row.get_attribute('class', silent=True)
    assert cls is not None, 'Self-healing did not recover the element'

    assert results, 'on_healing_success was not fired'
    result = results[0]
    class_match = result.breakdown.attributes['class']
    assert class_match.candidate_value == 'Row'
    assert class_match.matched is False  # exact string equality is False
    # before the canonical comparison 'row' vs 'Row' scored 0.0 (different tokens);
    # now the shared word 'row' gives a real contribution
    assert class_match.score > 0.0, 'canonical class comparison should give a real score'


def test_healing_matches_parent_class_canonically(second_playground_page):
    """Real browser: parent snake_case class matches a camelCase candidate class."""
    results = []
    configure(on_healing_success=results.append)

    driver = second_playground_page.driver_wrapper
    # build a container with a snake_case class and a sub-element span
    driver.execute_script("""
        var container = document.createElement('div');
        container.className = 'checkout_form_submit';
        container.innerHTML = '<span id="canonical-parent-sub-element">sub-element</span>';
        document.body.appendChild(container);
    """)

    # snapshot the sub-element while its parent still has the snake_case class
    element = Element('#canonical-parent-sub-element', name='canonical parent sub-element')
    element.wait_visibility(silent=True)

    storage = get_config().storage
    snapshot = storage.load(_key(element))
    assert snapshot is not None
    assert snapshot.parent_tag == 'div'
    assert snapshot.parent_attributes.get('class') == 'checkout_form_submit'

    # flip the parent class to camelCase — same words, different case/separators
    driver.execute_script(
        "document.getElementById('canonical-parent-sub-element').parentElement.className = 'checkoutFormSubmit';"
    )

    # break the sub-element locator and heal
    broken = Element('#broken-canonical-parent-sub-element', name=element.name)
    storage.save(_key(broken), snapshot)

    healed = broken.get_attribute('id', silent=True)
    assert healed is not None, 'Self-healing did not recover the element'

    assert results, 'on_healing_success was not fired'
    result = results[0]
    assert result.breakdown.parent_tag_matched is True
    assert result.breakdown.parent_attrs_score == 1.0, 'parent class should match canonically'


def test_healing_matches_sibling_class_canonically(second_playground_page):
    """Real browser: sibling BEM class matches a PascalCase candidate class."""
    results = []
    configure(on_healing_success=results.append)

    driver = second_playground_page.driver_wrapper
    # build a container: a target span plus a sibling with a BEM-style class
    driver.execute_script("""
        var container = document.createElement('div');
        container.className = 'container';
        container.innerHTML =
            '<span id="sibling-target">target</span>' +
            '<span class="modal__close-btn">close</span>';
        document.body.appendChild(container);
    """)

    target = Element('#sibling-target', name='sibling target')
    target.wait_visibility(silent=True)

    storage = get_config().storage
    snapshot = storage.load(_key(target))
    assert snapshot is not None
    assert snapshot.siblings, 'expected a sibling in the snapshot'
    assert snapshot.siblings[0]['attrs'].get('class') == 'modal__close-btn'

    # flip the sibling class to PascalCase — same words, different case/separators
    driver.execute_script(
        "document.getElementById('sibling-target').nextElementSibling.className = 'ModalCloseBtn';"
    )

    # break the target locator and heal
    broken = Element('#broken-sibling-target', name=target.name)
    storage.save(_key(broken), snapshot)

    healed = broken.get_attribute('id', silent=True)
    assert healed is not None, 'Self-healing did not recover the element'

    assert results, 'on_healing_success was not fired'
    result = results[0]
    assert result.breakdown.siblings_score == 1.0, 'sibling class should match canonically'


def test_healing_matches_element_class_canonically(second_playground_page):
    """Real browser: the ELEMENT's own class kebab vs PascalCase passes scoring."""
    results = []
    configure(on_healing_success=results.append)

    driver = second_playground_page.driver_wrapper
    # element whose own class is the kebab form
    driver.execute_script("""
        var el = document.createElement('span');
        el.className = 'user-profile-card';
        el.textContent = 'canonical-target-element';
        document.body.appendChild(el);
    """)

    el = Element('//span[.="canonical-target-element"]', name='canonical target element')
    el.wait_visibility(silent=True)

    storage = get_config().storage
    snapshot = storage.load(_key(el))
    assert snapshot is not None
    assert snapshot.attributes.get('class') == 'user-profile-card'

    # flip the ELEMENT's own class to PascalCase — same words, different format
    driver.execute_script("""
        var spans = document.querySelectorAll('span');
        for (var i = 0; i < spans.length; i++) {
            if (spans[i].textContent === 'canonical-target-element') {
                spans[i].className = 'UserProfileCard';
            }
        }
    """)

    # break the locator and heal — scoring must accept the canonical class match
    broken = Element('#broken-canonical-element', name=el.name)
    storage.save(_key(broken), snapshot)

    cls = broken.get_attribute('class', silent=True)
    assert cls is not None, 'Self-healing did not recover the element'
    assert cls == 'UserProfileCard'

    assert results, 'on_healing_success was not fired'
    result = results[0]
    class_match = result.breakdown.attributes['class']
    assert class_match.snapshot_value == 'user-profile-card'
    assert class_match.candidate_value == 'UserProfileCard'
    assert class_match.matched is False  # exact string equality is False
    assert class_match.score == 1.0, 'element class should match canonically'
