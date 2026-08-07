from __future__ import annotations

from unittest.mock import MagicMock

from mops.self_healing.healer import (
    Healer,
    _class_similarity,
    _class_to_tokens,
    _text_similarity,
)
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
        'siblings': [],
        **extra,
    }


def _make_storage():
    """Build a mock storage whose normalization is a no-op (candidates already clean)."""
    storage = MagicMock()
    storage.normalize_snapshot.side_effect = lambda snap: snap
    return storage


def _heal(storage, driver, threshold: float = 0.7, on_healing_failure=None):
    """Run heal() with mocked backend callbacks."""
    healer = Healer(storage, threshold, on_healing_failure=on_healing_failure)
    return healer.heal(
        'btn', 'key', '#submit', driver,
        find_elements_fn=lambda tag: driver.driver.find_elements('tag name', tag),
        generate_locator_fn=lambda *_: ['xpath=//button'],
    )


def _driver_with(candidates, elements):
    dw = MagicMock()
    dw.execute_script.return_value = candidates or []
    dw.driver.find_elements.return_value = elements or []
    return dw


# ---------------------------------------------------------------------------
# canonical CSS class comparison — word tokenization
# ---------------------------------------------------------------------------


def test_class_to_tokens_kebab_snake_camel_pascal():
    """Same meaning in different word styles produces the same token set."""
    # kebab-case <-> PascalCase
    assert _class_to_tokens('user-profile-card') == {'user', 'profile', 'card'}
    assert _class_to_tokens('UserProfileCard') == {'user', 'profile', 'card'}
    # snake_case <-> camelCase
    assert _class_to_tokens('checkout_form_submit') == {'checkout', 'form', 'submit'}
    assert _class_to_tokens('checkoutFormSubmit') == {'checkout', 'form', 'submit'}
    # BEM (__ separator) <-> PascalCase
    assert _class_to_tokens('modal__close-btn') == {'modal', 'close', 'btn'}
    assert _class_to_tokens('ModalCloseBtn') == {'modal', 'close', 'btn'}


def test_class_similarity_same_meaning_is_one():
    """Classes differing only in case/separators are the same class."""
    assert _class_similarity('user-profile-card', 'UserProfileCard') == 1.0
    assert _class_similarity('checkout_form_submit', 'checkoutFormSubmit') == 1.0
    assert _class_similarity('modal__close-btn', 'ModalCloseBtn') == 1.0


def test_class_similarity_partial_overlap():
    """Shared words give a score between 0 and 1."""
    score = _class_similarity('user-profile-card', 'user-profile-settings')
    assert 0.0 < score < 1.0


def test_class_similarity_distinct_is_zero():
    assert _class_similarity('avatar', 'submit-btn') == 0.0


def test_class_similarity_empty_is_zero():
    assert _class_similarity('', 'row') == 0.0


def test_healing_matches_class_with_different_case():
    """Element class differs in case/separators → canonical match, high score."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot(attributes={'class': 'user-profile-card'})
    driver = _driver_with(
        candidates=[_make_candidate(attrs={'class': 'UserProfileCard'})],
        elements=[MagicMock()],
    )

    result = _heal(storage, driver)

    assert result is not None
    class_match = result.breakdown.attributes['class']
    assert class_match.score == 1.0  # canonical comparison
    assert class_match.matched is False  # exact string equality is still False


def test_healing_parent_class_canonicalized():
    """Parent class differing in case/separators contributes a full parent score."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot(
        parent_tag='div',
        parent_attributes={'class': 'checkout_form_submit'},
    )
    driver = _driver_with(
        candidates=[_make_candidate(parentTag='div', parentAttrs={'class': 'checkoutFormSubmit'})],
        elements=[MagicMock()],
    )

    result = _heal(storage, driver)

    assert result is not None
    assert result.breakdown.parent_attrs_score == 1.0


def test_healing_sibling_class_canonicalized():
    """Sibling class differing in case/separators contributes a full sibling score."""
    snap_sib = {'tag': 'span', 'attrs': {'class': 'modal__close-btn'}, 'text': 'close'}
    cand_sib = {'tag': 'span', 'attrs': {'class': 'ModalCloseBtn'}, 'text': 'close'}
    storage = _make_storage()
    storage.load.return_value = _make_snapshot(siblings=[snap_sib])
    driver = _driver_with(
        candidates=[_make_candidate(siblings=[cand_sib])],
        elements=[MagicMock()],
    )

    result = _heal(storage, driver)

    assert result is not None
    assert result.breakdown.siblings_score == 1.0


# ---------------------------------------------------------------------------
# text similarity — no short-substring false positives
# ---------------------------------------------------------------------------


def test_text_similarity_exact_is_one():
    assert _text_similarity('Hello', 'hello') == 1.0


def test_text_similarity_short_substring_rejected():
    """'s' must not match any longer text."""
    assert _text_similarity('s', 'm_john_456') == 0.0


def test_text_similarity_two_char_substring_rejected():
    """'al' must not match 'alex'."""
    assert _text_similarity('al', 'alex') == 0.0


def test_text_similarity_word_substring_accepted():
    """'User' matches 'User: alex' as a whole word."""
    assert _text_similarity('User', 'User: alex') == 0.7


def test_text_similarity_substring_inside_underscored_rejected():
    """'alex' inside 'm_alex_123' is not a whole word."""
    assert _text_similarity('alex', 'm_alex_123') == 0.0


def test_healing_text_match_helps_target_over_short_avatar():
    """A single-char avatar text no longer steals the match via substring."""
    storage = _make_storage()
    storage.load.return_value = _make_snapshot(attributes={'id': 'x'}, text='User: alex')
    driver = MagicMock()
    driver.driver = MagicMock()
    driver.execute_script.return_value = [
        # target: shares tokens with the snapshot text
        _make_candidate(attrs={'id': 'x'}, text='User: john', parentTag='div'),
        # avatar: single char — must NOT match 'User: alex' as a substring anymore
        _make_candidate(attrs={'id': 'x'}, text='s', parentTag='div'),
    ]
    driver.driver.find_elements.return_value = [MagicMock()]

    result = _heal(storage, driver, threshold=0.0)

    assert result is not None
    assert result.breakdown.text_candidate == 'User: john'  # target wins, not the avatar
    assert result.breakdown.text_score is not None
    assert result.breakdown.text_score > 0.0


# ---------------------------------------------------------------------------
# DOM index drift protection
# ---------------------------------------------------------------------------
# TODO: the dom-changed-during-healing guard was temporarily removed from
# Healer.heal(). Re-add it together with these tests when index-drift
# protection is reintroduced.
