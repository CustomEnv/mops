from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Any

from mops.self_healing.locator_generator import generate_locator

if TYPE_CHECKING:
    from mops.self_healing.snapshot import ElementSnapshot, SnapshotStorage

logger = logging.getLogger('mops.self_healing')

_ATTRIBUTE_WEIGHTS: dict[str, float] = {
    'id': 1.0,
    'data-testid': 0.9,
    'data-test': 0.9,
    'data-cy': 0.9,
    'data-qa': 0.9,
    'data-automation-id': 0.9,
    'name': 0.7,
    'aria-label': 0.6,
    'placeholder': 0.5,
    'type': 0.4,
    'role': 0.3,
    'href': 0.3,
    'alt': 0.3,
    'title': 0.2,
    'class': 0.15,
}

_GET_CANDIDATES_JS = """
return (function(tag) {
    function getAttrs(node) {
        var attrs = {};
        for (var i = 0; i < node.attributes.length; i++) {
            attrs[node.attributes[i].name] = node.attributes[i].value;
        }
        return attrs;
    }
    var elements = document.getElementsByTagName(tag);
    var result = [];
    for (var i = 0; i < elements.length; i++) {
        var el = elements[i];
        var parent = el.parentElement;
        result.push({
            index: i,
            attrs: getAttrs(el),
            text: (el.textContent || '').trim().substring(0, 100),
            parentTag: parent ? parent.tagName.toLowerCase() : null,
            parentAttrs: parent ? getAttrs(parent) : {}
        });
    }
    return result;
})(arguments[0]);
"""


@dataclass
class HealingResult:
    element_name: str
    original_locator: str
    healed_locator: str
    score: float
    page: str | None = None


class Healer:
    """Orchestrates the self-healing process for a failed element lookup."""

    def __init__(self, storage: SnapshotStorage, score_threshold: float) -> None:
        self._storage = storage
        self._score_threshold = score_threshold

    def heal(self, element_name: str, locator_key: str, locator: str, driver: Any) -> HealingResult | None:
        """Try to find a healed locator for a failed element lookup.

        :param element_name: Human-readable element name for logging.
        :param locator_key: Storage key used to load the saved snapshot.
        :param locator: The original locator string (for the result record).
        :param driver: Selenium WebDriver instance.
        :return: :class:`HealingResult` if healed, ``None`` otherwise.
        """
        snapshot = self._storage.load(locator_key)
        if not snapshot:
            logger.debug('Self-healing: no snapshot for "%s", skipping', element_name)
            return None

        try:
            candidates_data: list[dict] = driver.execute_script(_GET_CANDIDATES_JS, snapshot.tag)
        except Exception as exc:
            logger.debug('Self-healing: failed to get candidates for "%s": %s', element_name, exc)
            return None

        if not candidates_data:
            return None

        best_score = 0.0
        best_index = -1

        for item in candidates_data:
            score = _score_similarity(item, snapshot)
            if score > best_score:
                best_score = score
                best_index = item['index']

        if best_score < self._score_threshold or best_index < 0:
            logger.debug(
                'Self-healing: best score %.2f below threshold %.2f for "%s"',
                best_score,
                self._score_threshold,
                element_name,
            )
            return None

        # Get the actual WebElement by index among elements of the same tag
        try:
            from selenium.webdriver.common.by import By

            web_elements = driver.find_elements(By.TAG_NAME, snapshot.tag)
            if best_index >= len(web_elements):
                return None
            healed_web_element = web_elements[best_index]
            healed_locator = generate_locator(healed_web_element, driver)
        except Exception as exc:
            logger.debug('Self-healing: failed to generate locator for "%s": %s', element_name, exc)
            return None

        result = HealingResult(
            element_name=element_name,
            original_locator=locator,
            healed_locator=healed_locator,
            score=best_score,
        )

        logger.info(
            'Self-healing: healed "%s"  %s -> %s  (score=%.2f)',
            element_name,
            locator,
            healed_locator,
            best_score,
        )

        return result


def _score_similarity(candidate: dict[str, Any], snapshot: ElementSnapshot) -> float:
    """Compute a 0–1 similarity score between a candidate DOM element and a saved snapshot."""
    score = 0.0
    total_weight = 0.0

    # Attribute matching
    for attr, weight in _ATTRIBUTE_WEIGHTS.items():
        snap_val = snapshot.attributes.get(attr)
        cand_val = candidate['attrs'].get(attr)

        if snap_val is None and cand_val is None:
            continue

        total_weight += weight

        if snap_val == cand_val:
            score += weight
        elif snap_val and cand_val:
            score += weight * _token_overlap(snap_val, cand_val)

    # Text similarity
    snap_text = snapshot.text
    cand_text = candidate.get('text', '')
    if snap_text:
        text_weight = 0.3
        total_weight += text_weight
        if snap_text == cand_text:
            score += text_weight
        elif snap_text and cand_text:
            score += text_weight * _text_similarity(snap_text, cand_text)

    # Parent tag match
    if snapshot.parent_tag and candidate.get('parentTag'):
        parent_weight = 0.2
        total_weight += parent_weight
        if candidate['parentTag'] == snapshot.parent_tag:
            score += parent_weight * 0.5
            parent_attr_score = _attrs_overlap(snapshot.parent_attributes, candidate.get('parentAttrs', {}))
            score += parent_weight * 0.5 * parent_attr_score

    if total_weight == 0:
        return 0.0

    return score / total_weight


def _token_overlap(a: str, b: str) -> float:
    """Jaccard token overlap for strings (e.g. CSS class lists)."""
    a_tokens = set(a.split())
    b_tokens = set(b.split())
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = a_tokens & b_tokens
    union = a_tokens | b_tokens
    return len(intersection) / len(union)


def _text_similarity(a: str, b: str) -> float:
    a_lower = a.lower()
    b_lower = b.lower()
    if a_lower == b_lower:
        return 1.0
    if a_lower in b_lower or b_lower in a_lower:
        return 0.7
    return _token_overlap(a_lower, b_lower)


def _attrs_overlap(snap_attrs: dict[str, str], cand_attrs: dict[str, str]) -> float:
    """Average match score across attributes present in the snapshot."""
    if not snap_attrs:
        return 0.0
    matches = sum(1 for k, v in snap_attrs.items() if cand_attrs.get(k) == v)
    return matches / len(snap_attrs)
