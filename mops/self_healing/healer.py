from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import re
from typing import TYPE_CHECKING, Any

from selenium.common.exceptions import WebDriverException

from mops.self_healing.snapshot import ElementSnapshot

if TYPE_CHECKING:
    from collections.abc import Callable

    from mops.self_healing.snapshot import SnapshotStorage

_MIN_SUBSTRING_LENGTH = 3
_CAMEL_BOUNDARY_RE = re.compile(r'([a-z0-9])([A-Z])')
_NON_WORD_RE = re.compile(r'[^a-zA-Z0-9]+')

logger = logging.getLogger('mops.self_healing')

_GET_CANDIDATES_JS = """
return (function(tag) {
    function getAttrs(node) {
        var attrs = {};
        for (var i = 0; i < node.attributes.length; i++) {
            attrs[node.attributes[i].name] = node.attributes[i].value;
        }
        return attrs;
    }
    function getSiblings(el) {
        var parent = el.parentElement;
        if (!parent) return [];
        var children = parent.children;
        var siblings = [];
        for (var i = 0; i < children.length && siblings.length < 5; i++) {
            if (children[i] !== el) {
                siblings.push({
                    tag: children[i].tagName.toLowerCase(),
                    text: (children[i].textContent || '').trim().substring(0, 50),
                    attrs: getAttrs(children[i])
                });
            }
        }
        return siblings;
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
            parentAttrs: parent ? getAttrs(parent) : {},
            siblings: getSiblings(el)
        });
    }
    return result;
})(arguments[0]);
"""


@dataclass
class ScoringWeights:
    """Tunable weights for the similarity scoring function.

    Each weight controls how much a signal contributes to the final 0-1 score.
    ``attribute`` is a per-attribute dict; the rest are scalar multipliers.
    """

    attribute: dict[str, float] = field(
        default_factory=lambda: {
            'id': 1.0,
            'name': 0.7,
            'placeholder': 0.5,
            'type': 0.4,
            'role': 0.3,
            'href': 0.3,
            'title': 0.2,
            'class': 0.15,
        }
    )
    text: float = 0.3
    parent: float = 0.2
    siblings: float = 0.15


@dataclass
class AttributeMatch:
    """Comparison of a single attribute between the snapshot and a DOM candidate.

    :param attribute: Attribute name (e.g. ``id``, ``class``).
    :param snapshot_value: Value saved in the snapshot, or ``None`` when the
        attribute is absent from the snapshot.
    :param candidate_value: Value found on the candidate element, or ``None``
        when the candidate does not have this attribute.
    :param matched: ``True`` when both values exist and are exactly equal.
    :param score: Similarity of the values — ``1.0`` on exact match, partial
        token overlap for weighted attributes, ``0.0`` otherwise.
    :param weight: Configured :class:`ScoringWeights` weight. ``0.0`` when the
        attribute does not participate in scoring (diagnostics only).
    """

    attribute: str
    snapshot_value: str | None
    candidate_value: str | None
    matched: bool
    score: float
    weight: float


@dataclass
class SimilarityBreakdown:
    """Per-signal similarity breakdown of one DOM candidate vs the snapshot.

    Exposed on :class:`SuccessHealingResult` and :class:`FailedHealingResult`
    for the best-scoring candidate so callers can see exactly which attributes
    matched and which did not — useful for spotting dynamic data (e.g. a
    changing ``id`` or a CSS-module hash in ``class``).

    :param candidate_snapshot: Raw DOM snapshot of the best candidate as found
        on the page. Unlike the normalized reference snapshot stored in the
        storage, this reflects the actual current state of the element — useful
        for comparing dynamic values side-by-side.
    """

    score: float
    attributes: dict[str, AttributeMatch]
    text_snapshot: str | None
    text_candidate: str | None
    text_score: float | None
    parent_tag_snapshot: str | None
    parent_tag_candidate: str | None
    parent_tag_matched: bool | None
    parent_attrs_score: float | None
    siblings_score: float | None
    siblings_snapshot_count: int
    siblings_candidate_count: int
    candidate_snapshot: ElementSnapshot | None = None

    @property
    def matched_attributes(self) -> list[str]:
        """Names of attributes that matched exactly."""
        return [attr for attr, match in self.attributes.items() if match.matched]

    @property
    def mismatched_attributes(self) -> list[str]:
        """Names of attributes that did not match exactly."""
        return [attr for attr, match in self.attributes.items() if not match.matched]


@dataclass
class SuccessHealingResult:
    element_name: str
    original_locator: str
    healed_locator: str | None
    healed_locators_candidates: list[str]
    score: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    breakdown: SimilarityBreakdown | None = None


@dataclass
class FailedHealingResult:
    element_name: str
    locator_key: str
    locator: str
    reason: str
    error: str | None = None
    best_score: float | None = None
    score_threshold: float | None = None
    candidates_count: int | None = None
    breakdown: SimilarityBreakdown | None = None


@dataclass
class HealingStats:
    """Process-wide self-healing counters.

    Updated automatically by the :class:`Healer` on every :meth:`Healer.heal` call.
    Read the current values with :func:`get_healing_stats`.

    .. note::
        ``healed`` counts candidates found by the Healer. A candidate can still
        fail DOM verification afterwards (``no-verified-locator``), which is
        reported via ``on_healing_failure`` but is not reflected in these
        counters — it happens outside the :class:`Healer`.
    """

    attempts: int = 0
    healed: int = 0
    failed: int = 0
    failed_reasons: dict[str, int] = field(default_factory=dict)
    _score_sum: float = 0.0
    _score_count: int = 0

    @property
    def avg_best_score(self) -> float | None:
        """Average best similarity score of successfully healed elements."""
        if self._score_count == 0:
            return None
        return self._score_sum / self._score_count


_stats = HealingStats()


def get_healing_stats() -> HealingStats:
    """Return process-wide self-healing statistics.

    Useful for end-of-run reporting, e.g. in ``pytest_sessionfinish``::

        from mops.self_healing import get_healing_stats

        def pytest_sessionfinish(session, exitstatus):
            stats = get_healing_stats()
            print(f'healing: {stats.healed} ok, {stats.failed} failed of {stats.attempts}')
    """
    return _stats


def _record_attempt() -> None:
    _stats.attempts += 1


def _record_heal_success(score: float) -> None:
    _stats.healed += 1
    _stats._score_sum += score
    _stats._score_count += 1


def _record_heal_failure(reason: str) -> None:
    _stats.failed += 1
    _stats.failed_reasons[reason] = _stats.failed_reasons.get(reason, 0) + 1


class Healer:
    """Orchestrates the self-healing process for a failed element lookup."""

    def __init__(
        self,
        storage: SnapshotStorage,
        score_threshold: float,
        scoring_weights: ScoringWeights | None = None,
        on_healing_failure: Callable[[FailedHealingResult], None] | None = None,
    ) -> None:
        self._storage = storage
        self._score_threshold = score_threshold
        self._scoring_weights = scoring_weights or ScoringWeights()
        self._on_healing_failure = on_healing_failure

    def _fail(
        self,
        reason: str,
        element_name: str,
        locator_key: str,
        locator: str,
        exc: BaseException | None = None,
        best_score: float | None = None,
        candidates_count: int | None = None,
        breakdown: SimilarityBreakdown | None = None,
    ) -> None:
        """Fire failure callback, record stats, and return None.

        :param best_score: Highest similarity score found before the failure,
            or ``None`` when no candidate was scored (e.g. no snapshot,
            script error, or empty candidate list).
        :param candidates_count: Number of DOM candidates scored, or ``None``
            when candidates were never collected.
        :param breakdown: Similarity breakdown of the best candidate, or
            ``None`` when no candidate was scored.
        """
        error: str | None = None
        if exc:
            error = exc.msg if isinstance(exc, WebDriverException) else str(exc)
        result = FailedHealingResult(
            element_name=element_name,
            locator_key=locator_key,
            locator=locator,
            reason=reason,
            error=error,
            best_score=best_score,
            score_threshold=self._score_threshold,
            candidates_count=candidates_count,
            breakdown=breakdown,
        )
        _record_heal_failure(reason)
        if self._on_healing_failure:
            self._on_healing_failure(result)

    def heal(
        self,
        element_name: str,
        locator_key: str,
        locator: str,
        driver_wrapper: Any,
        find_elements_fn: Callable[[str], list[Any]],
        generate_locator_fn: Callable[[Any, Any], list[str]],
    ) -> SuccessHealingResult | None:
        """Try to find a healed locator for a failed element lookup.

        :param element_name: Human-readable element name for logging.
        :param locator_key: Storage key used to load the saved snapshot.
        :param locator: The original locator string (for the result record).
        :param driver_wrapper: Driver wrapper with an ``execute_script(script, *args)`` method.
        :param find_elements_fn: Callback ``(tag: str) -> list`` to find all
            elements with a given tag name (backend-specific).
        :param generate_locator_fn: Callback ``(element, driver_wrapper) -> list[str]``
            to generate candidate locators from a live element (backend-specific).
        :return: :class:`SuccessHealingResult` if healed, ``None`` otherwise.
        """
        _record_attempt()
        snapshot = self._storage.load(locator_key)

        if not snapshot:
            logger.info('Self-healing: no snapshot for "%s", skipping', element_name)
            return self._fail('no-snapshot', element_name, locator_key, locator)

        candidates = self._collect_candidates(driver_wrapper, snapshot.tag, element_name, locator_key, locator)
        if candidates is None:
            return None

        scored = self._score_candidates(candidates, snapshot, element_name, locator_key, locator)
        if scored is None:
            return None

        best_score, best_index, best_breakdown = scored
        healed_locators = self._resolve_element(
            driver_wrapper,
            find_elements_fn,
            generate_locator_fn,
            snapshot.tag,
            best_index,
            best_score,
            best_breakdown,
            candidates,
            element_name,
            locator_key,
            locator,
        )
        if healed_locators is None:
            return None

        _record_heal_success(best_score)
        result = SuccessHealingResult(
            element_name=element_name,
            original_locator=locator,
            healed_locator=None,
            healed_locators_candidates=healed_locators,
            score=best_score,
            breakdown=best_breakdown,
        )

        logger.info(
            'Self-healing: healed "%s"  %s -> %s  (score=%.2f)',
            element_name,
            locator,
            healed_locators,
            best_score,
        )

        return result

    def _collect_candidates(
        self,
        driver_wrapper: Any,
        tag: str,
        element_name: str,
        locator_key: str,
        locator: str,
    ) -> list[dict] | None:
        """Collect DOM candidates of the same tag; returns ``None`` on failure."""
        try:
            candidates: list[dict] = driver_wrapper.execute_script(_GET_CANDIDATES_JS, tag)
        except WebDriverException as exc:
            logger.info('Self-healing: failed to get candidates for "%s": %s', element_name, exc)
            return self._fail('candidates-script-error', element_name, locator_key, locator, exc=exc)

        if not candidates:
            return self._fail('no-candidates', element_name, locator_key, locator, candidates_count=0)

        return candidates

    def _score_candidates(
        self,
        candidates_data: list[dict],
        snapshot: ElementSnapshot,
        element_name: str,
        locator_key: str,
        locator: str,
    ) -> tuple[float, int, SimilarityBreakdown] | None:
        """Score all candidates and return the best ``(score, index, breakdown)``.

        Returns ``None`` when the best score is below the threshold.
        """
        best_score = -1.0
        best_index = -1
        best_breakdown: SimilarityBreakdown | None = None

        for item in candidates_data:
            # Normalize the candidate with the same rules applied to snapshots,
            # so both sides of the comparison are cleaned equally.
            raw_candidate_snapshot = _candidate_to_snapshot(item, snapshot.tag)
            normalized_candidate_snapshot = self._storage.normalize_snapshot(raw_candidate_snapshot)

            breakdown = _compute_similarity_breakdown(
                normalized_candidate_snapshot,
                snapshot,
                self._scoring_weights,
                candidate_snapshot=raw_candidate_snapshot,
            )
            if breakdown.score > best_score:
                best_score = breakdown.score
                best_index = item['index']
                best_breakdown = breakdown

        if best_score < self._score_threshold or best_index < 0:
            logger.info(
                'Self-healing: best score %.2f below threshold %.2f for "%s"',
                best_score,
                self._score_threshold,
                element_name,
            )
            self._fail(
                'below-threshold',
                element_name,
                locator_key,
                locator,
                best_score=best_score,
                candidates_count=len(candidates_data),
                breakdown=best_breakdown,
            )
            return None

        return best_score, best_index, best_breakdown

    def _resolve_element(
        self,
        driver_wrapper: Any,
        find_elements_fn: Callable[[str], list[Any]],
        generate_locator_fn: Callable[[Any, Any], list[str]],
        tag: str,
        best_index: int,
        best_score: float,
        best_breakdown: SimilarityBreakdown | None,
        candidates_data: list[dict],
        element_name: str,
        locator_key: str,
        locator: str,
    ) -> list[str] | None:
        """Resolve the best-index element and generate locators for it.

        Returns the generated locator list, or ``None`` on failure (the failure
        callback is fired inside).
        """
        try:
            web_elements = find_elements_fn(tag)
            if best_index >= len(web_elements):
                self._fail(
                    'index-out-of-bounds',
                    element_name,
                    locator_key,
                    locator,
                    best_score=best_score,
                    candidates_count=len(candidates_data),
                    breakdown=best_breakdown,
                )
                return None
            healed_locators = generate_locator_fn(web_elements[best_index], driver_wrapper)
        except Exception as exc:  # noqa: BLE001
            logger.info('Self-healing: failed to generate locator for "%s": %s', element_name, exc)
            self._fail(
                'generate-locator-error',
                element_name,
                locator_key,
                locator,
                exc=exc,
                best_score=best_score,
                candidates_count=len(candidates_data),
                breakdown=best_breakdown,
            )
            return None

        if healed_locators is None:
            _record_heal_failure('no-generated-locator')
            return None

        return healed_locators


def _candidate_to_snapshot(candidate: dict[str, Any], tag: str) -> ElementSnapshot:
    """Convert a raw DOM candidate dict (from the candidates JS) into an ElementSnapshot."""
    return ElementSnapshot(
        tag=tag,
        attributes=candidate.get('attrs', {}),
        text=candidate.get('text', ''),
        parent_tag=candidate.get('parentTag'),
        parent_attributes=candidate.get('parentAttrs', {}),
        siblings=candidate.get('siblings', []),
    )


def _compute_similarity_breakdown(  # noqa: PLR0912
    candidate: ElementSnapshot,
    snapshot: ElementSnapshot,
    weights: ScoringWeights | None = None,
    candidate_snapshot: ElementSnapshot | None = None,
) -> SimilarityBreakdown:
    """Compute a similarity score and a per-signal breakdown for one candidate.

    The returned :class:`SimilarityBreakdown` contains the aggregate 0-1 ``score``
    plus an ``AttributeMatch`` for every snapshot attribute (and every weighted
    attribute) so callers can see which attributes matched and which did not.

    :param candidate: The normalized candidate snapshot to score — already cleaned
        with the same rules as *snapshot* (see :meth:`SnapshotStorage.normalize_snapshot`).
    :param candidate_snapshot: Optional raw (non-normalized) snapshot of the
        candidate as found on the page, attached to the breakdown for diagnostics.
        Defaults to *candidate*.
    """
    w = weights or ScoringWeights()
    score = 0.0
    total_weight = 0.0
    attributes: dict[str, AttributeMatch] = {}

    # Attribute matching — all snapshot attributes plus weighted ones present on
    # the candidate. Only weighted attributes contribute to the total score.
    weighted_attrs = set(w.attribute)
    for attr in set(snapshot.attributes) | weighted_attrs:
        snap_val = snapshot.attributes.get(attr)
        cand_val = candidate.attributes.get(attr)
        weight = w.attribute.get(attr, 0.0)

        if snap_val is None and cand_val is None:
            continue

        if weight:
            total_weight += weight
            attr_score = _attribute_similarity(attr, snap_val, cand_val, tag=snapshot.tag)
            score += weight * attr_score
        else:
            # Unweighted attribute — diagnostics only, binary match indicator
            attr_score = 1.0 if snap_val is not None and snap_val == cand_val else 0.0

        attributes[attr] = AttributeMatch(
            attribute=attr,
            snapshot_value=snap_val,
            candidate_value=cand_val,
            matched=snap_val is not None and snap_val == cand_val,
            score=attr_score,
            weight=weight,
        )

    # Text similarity
    snap_text = snapshot.text
    cand_text = candidate.text
    text_score: float | None = None
    if snap_text:
        total_weight += w.text
        if snap_text == cand_text:
            text_score = 1.0
        elif snap_text and cand_text:
            text_score = _text_similarity(snap_text, cand_text)
        else:
            text_score = 0.0
        score += w.text * text_score

    # Parent tag match. An empty ``snapshot.parent_attributes`` means the snapshot
    # carries no parent attribute info — that is an absence of data, not a
    # mismatch, so it is never penalized.
    parent_tag_matched: bool | None = None
    parent_attrs_score: float | None = None
    if snapshot.parent_tag and candidate.parent_tag:
        total_weight += w.parent
        parent_tag_matched = candidate.parent_tag == snapshot.parent_tag
        if parent_tag_matched:
            score += w.parent * 0.5
            if snapshot.parent_attributes:
                parent_attrs_score = _attrs_overlap(snapshot.parent_attributes, candidate.parent_attributes)
                score += w.parent * 0.5 * parent_attrs_score

    # Sibling similarity is optional: a candidate may lose its siblings entirely
    # (e.g. a new React wrapper), so an empty candidate sibling list is treated as
    # missing data rather than a mismatch.
    snap_siblings = snapshot.siblings
    cand_siblings = candidate.siblings
    siblings_score: float | None = None
    if snap_siblings and cand_siblings:
        total_weight += w.siblings
        siblings_score = _siblings_similarity(snap_siblings, cand_siblings)
        score += w.siblings * siblings_score

    final_score = 0.0 if total_weight == 0 else score / total_weight

    if candidate_snapshot is None:
        candidate_snapshot = candidate

    return SimilarityBreakdown(
        score=final_score,
        attributes=attributes,
        text_snapshot=snap_text,
        text_candidate=cand_text,
        text_score=text_score,
        parent_tag_snapshot=snapshot.parent_tag,
        parent_tag_candidate=candidate.parent_tag,
        parent_tag_matched=parent_tag_matched,
        parent_attrs_score=parent_attrs_score,
        siblings_score=siblings_score,
        siblings_snapshot_count=len(snap_siblings),
        siblings_candidate_count=len(cand_siblings),
        candidate_snapshot=candidate_snapshot,
    )


def _token_overlap(a: str, b: str) -> float:
    """Jaccard token overlap for strings (e.g. space-separated value lists)."""
    a_tokens = set(a.split())
    b_tokens = set(b.split())
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = a_tokens & b_tokens
    union = a_tokens | b_tokens
    return len(intersection) / len(union)


def _class_to_tokens(class_str: str) -> set[str]:
    """Split a CSS class into canonical lowercase word tokens.

    Handles kebab-case, snake_case, camelCase, PascalCase and BEM/CSS-module
    separators (``_``, ``__``, ``--``)::

        'user-profile-card'    -> {'user', 'profile', 'card'}
        'UserProfileCard'      -> {'user', 'profile', 'card'}
        'checkout_form_submit' -> {'checkout', 'form', 'submit'}
        'checkoutFormSubmit'   -> {'checkout', 'form', 'submit'}
        'modal__close-btn'     -> {'modal', 'close', 'btn'}
        'ModalCloseBtn'        -> {'modal', 'close', 'btn'}

    So classes that only differ in case or word separators compare as equal.
    """
    # split camelCase / PascalCase word boundaries first
    split_case = _CAMEL_BOUNDARY_RE.sub(r'\1 \2', class_str)
    # then split on any non-alphanumeric separator (kebab, snake, __, ...)
    tokens = _NON_WORD_RE.split(split_case)
    return {token.lower() for token in tokens if token}


def _class_similarity(a: str, b: str) -> float:
    """Jaccard similarity of two CSS classes after canonical word tokenization."""
    a_tokens = _class_to_tokens(a)
    b_tokens = _class_to_tokens(b)
    if not a_tokens or not b_tokens:
        return 0.0
    if a_tokens == b_tokens:
        return 1.0
    intersection = a_tokens & b_tokens
    union = a_tokens | b_tokens
    return len(intersection) / len(union)


_HTML_DEFAULT_ATTRS: dict[str, dict[str, str]] = {
    'input': {'type': 'text'},
    'button': {'type': 'submit'},
    'script': {'type': 'text/javascript'},
    'style': {'type': 'text/css'},
    'link': {'type': 'text/css'},
    'ol': {'type': '1'},
}


def _attribute_similarity(
    attr: str,
    snap_val: str | None,
    cand_val: str | None,
    tag: str | None = None,
) -> float:
    """0-1 similarity of a single attribute value between snapshot and candidate.

    ``class`` uses canonical word-token comparison; everything else falls back to
    exact match (``1.0``) or token overlap for partial matches.

    HTML defaults are applied when *tag* is known: e.g. an ``<input>`` without a
    ``type`` attribute is ``type="text"``, a ``<button>`` without ``type`` is
    ``type="submit"`` — so a candidate missing the attribute matches the
    snapshot's default value.
    """
    if snap_val is None or cand_val is None:
        defaults = _HTML_DEFAULT_ATTRS.get(tag or '')
        if defaults and attr in defaults and snap_val == defaults[attr]:
            return 1.0  # HTML default for <tag>
        return 0.0
    if snap_val == cand_val:
        return 1.0
    if attr == 'class':
        return _class_similarity(snap_val, cand_val)
    return _token_overlap(snap_val, cand_val)


def _text_similarity(a: str, b: str) -> float:
    """0-1 text similarity without short-substring false positives."""
    a_lower = a.lower()
    b_lower = b.lower()
    if a_lower == b_lower:
        return 1.0
    # Substring matches are only meaningful for longer strings and must respect
    # word boundaries — otherwise 's' or 'al' would match any longer text.
    if (
        len(a_lower) >= _MIN_SUBSTRING_LENGTH
        and len(b_lower) >= _MIN_SUBSTRING_LENGTH
        and (_is_word_substring(a_lower, b_lower) or _is_word_substring(b_lower, a_lower))
    ):
        return 0.7
    return _token_overlap(a_lower, b_lower)


def _is_word_substring(short: str, long: str) -> bool:
    """Return True when *short* appears in *long* as a whole word."""
    return re.search(rf'\b{re.escape(short)}\b', long) is not None


def _attrs_overlap(snap_attrs: dict[str, str], cand_attrs: dict[str, str]) -> float:
    """Average match score across attributes present in the snapshot.

    Uses the same per-attribute comparator as element scoring, so e.g. ``class``
    values that differ only in case/separators still contribute.
    """
    if not snap_attrs:
        return 0.0
    total = sum(
        _attribute_similarity(k, v, cand_attrs.get(k)) for k, v in snap_attrs.items() if cand_attrs.get(k) is not None
    )
    return total / len(snap_attrs)


def _siblings_similarity(snap_siblings: list[dict], cand_siblings: list[dict]) -> float:
    """Compute 0-1 similarity between two sets of sibling elements."""
    if not snap_siblings:
        return 0.0

    total = 0.0
    for snap_sib in snap_siblings:
        best = 0.0
        for cand_sib in cand_siblings:
            tag_match = 1.0 if snap_sib.get('tag') == cand_sib.get('tag') else 0.0
            attr_score = _attrs_overlap(snap_sib.get('attrs', {}), cand_sib.get('attrs', {}))
            score = tag_match * 0.3 + attr_score * 0.7
            best = max(best, score)
        total += best

    return total / len(snap_siblings)
