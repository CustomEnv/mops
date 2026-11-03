"""Backend-agnostic self-healing orchestration.

:class:`HealingMixin` holds the whole healing flow — attempt, parent recovery,
locator verification — so that engine modules (``core_element``, ``play_element``)
only keep thin backend hooks instead of duplicating the process.

Backends must override the ``_healing_*`` hooks:

* :meth:`_healing_find_elements_by_tag` — all elements with a given tag
* :meth:`_healing_generate_locator` — locator candidates for a live element
* :meth:`_healing_parse_locator` — turn a candidate string into a backend selector
* :meth:`_healing_find_matches` — resolve a selector to individual elements
* :meth:`_healing_try_original_locator` — re-check the original locator
* :meth:`_healing_score_element` — similarity of a live element to the snapshot
* :meth:`_healing_apply_locator` — persist a verified locator on the element

and may set :attr:`_healing_lookup_exceptions` to the exceptions that mean
"lookup miss" for the engine (skipped candidate).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mops.exceptions import NoSuchElementException, NoSuchParentException
from mops.self_healing.config import get_config
from mops.self_healing.healer import MAX_HEALING_DEPTH, FailedHealingResult, SuccessHealingResult
from mops.self_healing.healer_factory import get_healer

if TYPE_CHECKING:
    from mops.self_healing.snapshot import ElementSnapshot


_UNRESOLVED = object()


class HealingMixin:
    """Self-healing locator orchestration shared by all element backends."""

    #: Exceptions raised by a backend lookup that simply mean "no match".
    _healing_lookup_exceptions: tuple[type[BaseException], ...] = ()

    # Backend hooks

    def _healing_find_elements_by_tag(self, tag: str, base: Any) -> list[Any]:
        """Return all elements with the given tag name inside *base*."""
        raise NotImplementedError

    def _healing_scope(self, base: Any) -> Any:
        """Return the JS scope object limiting the candidate scan to *base*, or :obj:`None`."""
        raise NotImplementedError

    def _healing_generate_locator(self, element: Any, driver_wrapper: Any) -> list[str]:
        """Generate ordered locator candidates for a live element."""
        raise NotImplementedError

    def _healing_parse_locator(self, locator: str) -> Any:
        """Turn a generated locator (``xpath=//...``) into a backend selector."""
        raise NotImplementedError

    def _healing_find_matches(self, base: Any, selector: Any) -> list[Any]:
        """Resolve a selector to individual element handles (bounded by ``max_verify_matches``)."""
        raise NotImplementedError

    def _healing_try_original_locator(self, base: Any) -> Any:
        """Return the resolved element when the current locator works again, else :obj:`None`."""
        raise NotImplementedError

    def _healing_score_element(self, element: Any, snapshot: ElementSnapshot, config: Any) -> float | None:
        """Return the similarity of a live element to the reference snapshot."""
        raise NotImplementedError

    def _healing_apply_locator(self, selector: Any, element: Any) -> None:
        """Persist a verified locator (and the resolved element) on the element object."""
        raise NotImplementedError

    # Healing flow

    def _attempt_healing(self, base: Any) -> SuccessHealingResult | None:
        """Attempt to heal a failed element lookup using the self-healing subsystem.

        Candidate search is scoped to *base* (the parent container when the element is
        nested), mirroring how MOPS resolves a regular locator. Both the JS scan and
        the element lookup use the same scope, so candidate indices stay consistent.

        :param base: Resolved search context — a driver/page at root, or a parent element.
        :return: :class:`SuccessHealingResult` if a suitable candidate was found, :obj:`None` otherwise.
        """
        try:
            healer = get_healer()
            locator_key = get_config().storage.extract_full_locator_key(self)
            result = healer.heal(
                element_name=self.name,
                locator_key=locator_key,
                locator=self.locator,
                driver_wrapper=self.driver_wrapper,
                find_elements_fn=lambda tag: self._healing_find_elements_by_tag(tag, base),
                generate_locator_fn=self._healing_generate_locator,
                scope=self._healing_scope(base),
            )
            if type(result) is SuccessHealingResult:
                return result
        except Exception as exc:  # noqa: BLE001
            self.log(f'Self-healing failed with unexpected exception: {exc}', level='warning')
            return None
        return None

    def _resolve_base(self, depth: int) -> tuple[Any, str | None]:
        """Resolve the base (parent) context, healing a missing parent first.

        Returns a ``(base, error)`` pair; *base* is ``None`` (with an error message)
        when the parent could not be resolved even after healing.
        """
        try:
            return self._get_base(wait_strategy=False), None
        except (NoSuchElementException, NoSuchParentException) as exc:
            # Parent is missing — heal it first, then retry inside the healed context.
            if depth < MAX_HEALING_DEPTH and self.parent is not None and self.parent._apply_healing(depth + 1):
                try:
                    return self._get_base(wait_strategy=False), None
                except (NoSuchElementException, NoSuchParentException) as exc2:
                    return None, str(exc2)
            return None, str(exc)

    def _try_healed_locators(
        self,
        result: SuccessHealingResult | None = None,
        depth: int = 0,
        base: Any = _UNRESOLVED,
    ) -> Any:
        """Resolve the search context, heal it if missing, then verify healed locators.

        Order matters: the candidate search must run *inside* the resolved base, so a
        nested element heals within its (possibly healed) parent container rather than
        against the whole document. When the parent is itself missing, it is healed
        first — recursively, so a chain of missing ancestors is healed from the top down
        (bounded by :data:`MAX_HEALING_DEPTH`).

        A healing attempt always ends with a terminal callback: ``on_healing_success``
        when a candidate passes DOM verification, or ``on_healing_failure`` otherwise
        (including when verification itself fails or cannot be performed).

        :param result: Pre-computed healing result, or :obj:`None` to attempt healing here.
        :param depth: Recursion depth guard for healing missing parents.
        :param base: Already resolved search context, bypassing resolution when given.
        :return: The resolved element.
        :raises NoSuchElementException: If no candidate locator passes verification.
        """
        config = get_config()

        if base is _UNRESOLVED:
            base, error = self._resolve_base(depth)
        else:
            error = None

        if base is not None:
            # Try the ORIGINAL locator first — the DOM may have settled while
            # healing was running (e.g. async re-render) and it could work again.
            # If it does, no healing actually happened, so no metrics are emitted.
            try:
                original = self._healing_try_original_locator(base)
            except self._healing_lookup_exceptions:
                original = None

            if original is not None:
                self.log(f'Self-healing: original locator "{self.locator}" works again for "{self.name}"')
                return original

            if result is None:
                result = self._attempt_healing(base)
                if result is None and error is None:
                    error = 'Self-healing produced no candidate locators'

            if result is not None:
                try:
                    healed = self._verify_healed_locators(base, result, config)
                except Exception as exc:  # noqa: BLE001
                    healed = None
                    error = exc.msg if hasattr(exc, 'msg') else str(exc)
                if healed is not None:
                    return healed
                if error is None:
                    error = 'All healed locator candidates failed DOM verification'

        # Terminal failure — no candidate passed DOM verification
        self._fire_failure(result, error)
        msg = error or 'Healed locator candidates did not match any element'
        raise NoSuchElementException(msg)

    def _fire_failure(self, result: SuccessHealingResult | None, error: str | None) -> None:
        """Emit the terminal ``on_healing_failure`` callback for a failed heal."""
        config = get_config()
        if not config.on_healing_failure:
            return

        config.on_healing_failure(
            FailedHealingResult(
                element_name=result.element_name if result else self.name,
                locator_key=result.locator_key if result else '',
                locator=result.original_locator if result else self.locator,
                reason='no-verified-locator',
                error=error,
                best_score=result.score if result else None,
                score_threshold=config.score_threshold,
                candidates_count=result.candidates_count if result else None,
                breakdown=result.breakdown if result else None,
            )
        )

    def _verify_healed_locators(self, base: Any, result: SuccessHealingResult, config: Any) -> Any:
        """Try each healed locator against *base*; persist and callback the first verified hit.

        Generated locators are frequently not unique (e.g. ``//input[@type="text"]``),
        so a locator resolving is not proof that it resolved to the element the healer
        scored. A locator matching exactly one element is accepted as-is; when it matches
        several, only the match whose live snapshot is most similar to the reference
        snapshot is accepted, and only above ``min_verify_score``.
        """
        for locator in result.healed_locators_candidates:
            selector = self._healing_parse_locator(locator)
            try:
                matches = self._healing_find_matches(base, selector)
            except self._healing_lookup_exceptions:
                continue

            if not matches:
                continue

            healed = matches[0] if len(matches) == 1 else self._pick_verified_healed(matches, result, config)
            if healed is None:
                continue

            result.healed_locator = locator
            self._healing_apply_locator(selector, healed)
            self.log(f'Self-healing: healed "{self.name}" with locator "{locator}"')
            # Fire success callback AFTER locator is verified against DOM
            if config.on_healing_success:
                config.on_healing_success(result)
            return healed
        return None

    def _pick_verified_healed(self, matches: list[Any], result: SuccessHealingResult, config: Any) -> Any:
        """Return the match most similar to the reference snapshot, or :obj:`None`.

        Used when a healed locator is not unique: picking the first match would risk
        acting on a different element than the one that was scored.
        """
        if result.snapshot is None:
            return None

        threshold = getattr(config, 'min_verify_score', None)
        if threshold is None:
            threshold = config.score_threshold

        best_element: Any = None
        best_score = 0.0
        for element in matches:
            score = self._healing_score_element(element, result.snapshot, config)
            if score and score > best_score:
                best_element, best_score = element, score

        if best_element is None or best_score < threshold:
            return None

        result.score = best_score
        return best_element

    def _apply_healing(self, depth: int = 0) -> bool:
        """Attempt healing and persist the first verified locator.

        Called by :func:`@healing <mops.utils.decorators.healing>` and
        :func:`@healing_after_wait <mops.utils.decorators.healing_after_wait>`.

        :param depth: Recursion depth guard used when a parent needs to be healed
            first so the element can be verified inside the healed parent context.
        :return: :obj:`True` if a healed locator was found and applied.
        """
        try:
            self._try_healed_locators(depth=depth)
        except NoSuchElementException:
            return False
        return True

    def _heal_after_wait(self) -> bool:
        """Attempt healing after a wait condition timed out.

        Persists the first working healed locator so subsequent lookups
        use it directly.

        :return: :obj:`True` if a working locator was found.
        """
        return self._apply_healing()
