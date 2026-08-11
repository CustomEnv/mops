from __future__ import annotations

import re
from types import SimpleNamespace

from mops.self_healing.snapshot import ElementSnapshot, JsonFileSnapshotStorage

# ---------------------------------------------------------------------------
# _extract_full_locator_key
# ---------------------------------------------------------------------------


def _make_element(name: str, locator: str, parent=None):
    """Build a minimal fake element for key-extraction tests."""
    return SimpleNamespace(name=name, locator=locator, parent=parent)


def test_extract_key_without_parent():
    """Element without parent uses name::locator (or bare locator if name matches)."""
    storage = JsonFileSnapshotStorage()

    # name != locator → name::locator
    el = _make_element('Submit button', '#submit')
    assert storage.extract_full_locator_key(el) == 'Submit button::#submit'

    # name == locator → bare locator
    el = _make_element('.row', '.row')
    assert storage.extract_full_locator_key(el) == '.row'


def test_extract_key_with_parent():
    """Parent context is appended with ' -> ' separator."""
    storage = JsonFileSnapshotStorage()

    grandparent = _make_element('Section', '#section')
    parent = _make_element('Form', '#form', parent=grandparent)
    element = _make_element('Submit button', '#submit', parent=parent)

    result = storage.extract_full_locator_key(element)
    assert result == 'Submit button::#submit -> Form::#form -> Section::#section'


def test_extract_key_with_parent_normalized():
    """Dynamic data in any part of the chain is normalized."""
    storage = JsonFileSnapshotStorage()

    # The default class-only rules don't affect locator keys (token-removal skipped),
    # so no normalization happens with defaults. But custom rules should apply.
    parent = _make_element('Form', '#form')
    element = _make_element('User card', '#user-12345', parent=parent)

    # Default rules don't strip #user-12345 because id rules were removed
    result = storage.extract_full_locator_key(element)
    assert 'User card::#user-12345' in result


# ---------------------------------------------------------------------------
# normalize_locator_key
# ---------------------------------------------------------------------------


def test_normalize_locator_key_preserves_clean_key():
    """Locator without dynamic data stays unchanged."""
    storage = JsonFileSnapshotStorage()
    assert storage.normalize_locator_key('MyElement::.row') == 'MyElement::.row'


def test_normalize_locator_key_class_removal_rules_skipped():
    """Token-removal rules (replacement=None) are not applied to locator keys."""
    storage = JsonFileSnapshotStorage()
    result = storage.normalize_locator_key('MyElement::.btn.active')
    assert 'active' in result


# ---------------------------------------------------------------------------
# _normalize_attrs — class token removal
# ---------------------------------------------------------------------------


def test_normalize_attrs_removes_css_module_hash_from_class():
    """Button_nameHash__xy tokens removed from class attribute."""
    storage = JsonFileSnapshotStorage()
    attrs = {'class': 'Button_1a2b3__xy another-class'}
    result = storage._normalize_attrs(attrs)
    assert result['class'] == 'another-class'


def test_normalize_attrs_removes_hash_suffix_from_class():
    r"""``#sb`` / ``#rdT`` tokens removed from class."""
    storage = JsonFileSnapshotStorage()
    attrs = {'class': 'some-class #sb'}
    result = storage._normalize_attrs(attrs)
    assert result['class'] == 'some-class'


def test_normalize_attrs_removes_dynamic_state_classes():
    """Exact-match state tokens (active / disabled / selected / open / closed) removed."""
    storage = JsonFileSnapshotStorage()
    attrs = {'class': 'btn active disabled js-toggle'}
    result = storage._normalize_attrs(attrs)
    assert result['class'] == 'btn js-toggle'


def test_normalize_attrs_preserves_normal_class():
    """Meaningful class names survive."""
    storage = JsonFileSnapshotStorage()
    attrs = {'class': 'btn btn-primary header'}
    result = storage._normalize_attrs(attrs)
    assert result['class'] == 'btn btn-primary header'


# ---------------------------------------------------------------------------
# _normalize_attrs — edge cases
# ---------------------------------------------------------------------------


def test_normalize_attrs_empty():
    """Empty dict stays empty."""
    storage = JsonFileSnapshotStorage()
    assert storage._normalize_attrs({}) == {}


def test_normalize_attrs_unknown_attrs_preserved():
    """Attributes without matching rules are preserved."""
    storage = JsonFileSnapshotStorage()
    attrs = {'aria-label': 'Close', 'id': 'submit-btn', 'data-test': 'submit'}
    result = storage._normalize_attrs(attrs)
    assert result == attrs


# ---------------------------------------------------------------------------
# _normalize_snapshot — full snapshot normalization
# ---------------------------------------------------------------------------


def test_normalize_snapshot_cleans_attrs_and_text():
    """Full snapshot normalization works across all fields."""
    storage = JsonFileSnapshotStorage()
    snapshot = ElementSnapshot(
        tag='button',
        attributes={
            'class': 'btn active #sb',
            'id': 'submit-42',
            'aria-label': 'Submit',
        },
        text='  Click  Me  ',
        parent_tag='form',
        parent_attributes={
            'class': 'form-wrapper js-form',
        },
        siblings=[
            {'tag': 'span', 'text': 'Hint', 'attrs': {'class': 'helper #rdT'}},
        ],
    )
    result = storage.normalize_snapshot(snapshot)
    assert result.tag == 'button'
    # Class tokens cleaned (active and #sb removed)
    assert result.attributes['class'] == 'btn'
    # id has no default rule — preserved (was removed from defaults by user)
    assert result.attributes['id'] == 'submit-42'
    # Non-matching attrs preserved
    assert result.attributes['aria-label'] == 'Submit'
    # Text whitespace normalized
    assert result.text == 'Click Me'
    # Parent attrs: ``js-form`` not exact match for ``^(js-|...)`` — kept
    assert result.parent_attributes['class'] == 'form-wrapper js-form'
    # Sibling attrs cleaned
    assert result.siblings[0]['attrs']['class'] == 'helper'


def test_normalize_snapshot_without_parent():
    """Snapshot with no parent does not crash."""
    storage = JsonFileSnapshotStorage()
    snapshot = ElementSnapshot(
        tag='div',
        attributes={'class': 'box'},
        text='content',
        parent_tag=None,
        parent_attributes={},
        siblings=[],
    )
    result = storage.normalize_snapshot(snapshot)
    assert result.parent_tag is None


# ---------------------------------------------------------------------------
# custom normalization rules
# ---------------------------------------------------------------------------


def test_custom_rules_extend_defaults():
    """External projects can extend default rules."""
    storage = JsonFileSnapshotStorage()
    storage.set_normalization_rules([
        *storage._normalization_rules,
        ('data-track', re.compile(r'.*'), ''),
    ])
    attrs = {'class': 'btn', 'data-track': 'some-value'}
    result = storage._normalize_attrs(attrs)
    assert result['class'] == 'btn'
    assert 'data-track' not in result


def test_custom_rules_apply_to_locator_key():
    """Custom string-replacement rules affect normalize_locator_key too."""
    storage = JsonFileSnapshotStorage()
    storage.set_normalization_rules([
        (None, re.compile(r'custom-'), ''),
    ])
    assert storage.normalize_locator_key('El::#custom-123') == 'El::#123'


def test_custom_rules_affect_extracted_key():
    """Custom rules also apply to _extract_full_locator_key via normalize_locator_key."""
    storage = JsonFileSnapshotStorage()
    storage.set_normalization_rules([
        (None, re.compile(r'-\d+'), ''),
    ])
    parent = _make_element('Form', '#form-99')
    element = _make_element('User card', '#user-12345', parent=parent)

    result = storage.extract_full_locator_key(element)
    assert result == 'User card::#user -> Form::#form'
