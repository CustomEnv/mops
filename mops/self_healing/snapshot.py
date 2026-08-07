from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from mops.base.element import Element


def _extract_full_locator_key(element: Element, normalize_fn: Callable[[str], str]) -> str:
    """Build the full hierarchical locator key for an element.

    :param element: The MOPS Element.
    :param normalize_fn: A function that normalizes a raw key string (e.g. removes dynamic data).
    :return: Normalized composite key like ``Name::locator -> ParentName::parent_locator``.
    """
    raw_locator_key = element.locator if element.name == element.locator else f'{element.name}::{element.locator}'

    if element.parent:
        raw_locator_key += f' -> {_extract_full_locator_key(element.parent, normalize_fn)}'

    return normalize_fn(raw_locator_key)


@dataclass
class ElementSnapshot:
    """Snapshot of a successfully located element's DOM context."""

    tag: str
    attributes: dict[str, str]
    text: str
    parent_tag: str | None
    parent_attributes: dict[str, str]
    siblings: list[dict[str, Any]]


_MAX_FILENAME_LENGTH = 200
_FILENAME_HASH_SUFFIX_LENGTH = 12

_GET_ELEMENT_SNAPSHOT_JS = """
return (function(el) {
    function getAttrs(node) {
        var attrs = {};
        for (var i = 0; i < node.attributes.length; i++) {
            attrs[node.attributes[i].name] = node.attributes[i].value;
        }
        return attrs;
    }
    var parent = el.parentElement;
    var parentTag = null;
    var parentAttrs = {};
    var siblings = [];
    if (parent) {
        parentTag = parent.tagName.toLowerCase();
        parentAttrs = getAttrs(parent);
        var children = parent.children;
        for (var i = 0; i < children.length && siblings.length < 5; i++) {
            if (children[i] !== el) {
                siblings.push({
                    tag: children[i].tagName.toLowerCase(),
                    text: (children[i].textContent || '').trim().substring(0, 50),
                    attrs: getAttrs(children[i])
                });
            }
        }
    }
    return {
        tag: el.tagName.toLowerCase(),
        attrs: getAttrs(el),
        text: (el.textContent || '').trim().substring(0, 100),
        parentTag: parentTag,
        parentAttrs: parentAttrs,
        siblings: siblings
    };
})(arguments[0]);
"""


# Each rule: (attribute_name, compiled_regex, replacement)
# - attribute_name: attribute to apply to, or None for text
# - replacement: None means token-removal (split by spaces, drop matching tokens),
#   '' means remove attribute entirely, str means re.sub(replacement)
_DEFAULT_NORMALIZATION_RULES: list[tuple[str | None, re.Pattern, str | None]] = [
    # CSS-module hashes: Button_nameHash__xy
    ('class', re.compile(r'[a-zA-Z]+[_-][a-fA-F0-9]{5,10}__[a-zA-Z0-9]{1,5}'), None),
    # Auto-generated suffixes: #sb, #rdT
    ('class', re.compile(r'^#\w{1,10}$'), None),
    # Dynamic/state classes aligned with locator_generator._DYNAMIC_CLASS_PREFIXES
    ('class', re.compile(r'^(js-|is-|has-|active|disabled|selected|open|closed)$'), None),
]


class SnapshotStorage(ABC):
    """Abstract snapshot storage for element snapshots.

    Subclasses must implement :meth:`save` and :meth:`load`.
    The :meth:`save_from_element` method is concrete — it extracts DOM data
    from a live web element and delegates to :meth:`save` for persistence.
    """

    def __init__(self) -> None:
        self._saved_this_session: set[str] = set()
        self._normalization_rules = list(_DEFAULT_NORMALIZATION_RULES)

    def _extract_full_locator_key(self, element: Element) -> str:
        """Use :meth:`extract_full_locator_key` instead."""
        return self.extract_full_locator_key(element)

    def extract_full_locator_key(self, element: Element) -> str:
        """Build the full hierarchical locator key for an element.

        :param element: The MOPS Element.
        :return: Normalized composite key like ``Name::locator -> ParentName::parent_locator``.
        """
        return _extract_full_locator_key(element, self.normalize_locator_key)

    def save_from_element(self, element: Element, web_element: object, driver: object) -> None:
        """Extract snapshot from a live web element and persist it."""
        locator_key = self.extract_full_locator_key(element)

        if locator_key in self._saved_this_session:
            return

        try:
            raw = driver.execute_script(_GET_ELEMENT_SNAPSHOT_JS, web_element)
        except Exception:  # noqa: BLE001
            return

        snapshot = ElementSnapshot(
            tag=raw['tag'],
            attributes=raw['attrs'],
            text=raw['text'],
            parent_tag=raw['parentTag'],
            parent_attributes=raw['parentAttrs'],
            siblings=raw['siblings'],
        )

        snapshot = self.normalize_snapshot(snapshot)
        self.save(locator_key, snapshot)
        self._saved_this_session.add(locator_key)

    def set_normalization_rules(self, rules: list[tuple[str | None, re.Pattern, str | None]]) -> None:
        """Replace the default normalization rules with custom ones.

        Each rule is ``(attribute_name_or_None, compiled_regex, replacement)``:

        * ``attribute_name`` — attribute key to match (``'class'``, ``'id'``, etc.)
          or ``None`` to match any attribute name.
        * ``compiled_regex`` — compiled :class:`re.Pattern` to match against the
          attribute value (or token, in token-removal mode).
        * ``replacement`` — if ``None``, the rule runs in **token-removal mode**
          (value is split on whitespace, matching tokens are dropped). If a string,
          ``regex.sub(replacement, value)`` is applied. If the result is empty,
          the attribute is removed entirely.

        Calling this method replaces **all** rules. To extend defaults::

            storage = JsonFileSnapshotStorage()
            storage.set_normalization_rules([
                *storage._normalization_rules,
                ('data-track', re.compile(r'.*'), ''),
            ])
        """
        self._normalization_rules = list(rules)

    def normalize_locator_key(self, key: str) -> str:
        r"""Normalize dynamic data in a locator key string.

        Applies all rules where ``replacement`` is a string (not ``None``).
        Token-removal rules (``replacement=None``) are skipped since a locator
        key is a flat string, not a whitespace-separated list of tokens.

        Calling this ensures that e.g. ``#user-12345`` and ``#user-67890``
        produce the same storage key when a ``-\d+`` rule is configured.
        """
        for _attr_name, pattern, replacement in self._normalization_rules:
            if replacement is None:
                continue  # skip token-removal rules
            key = pattern.sub(replacement, key)
        return key

    def normalize_snapshot(self, snapshot: ElementSnapshot) -> ElementSnapshot:
        """Return a normalized copy of *snapshot* with dynamic data cleaned out.

        This is applied both when a snapshot is saved (so the reference stored
        in the storage is clean) and to DOM candidates during healing — so both
        sides of the similarity comparison use the same normalization rules.

        External projects can plug their own cleanup via
        :meth:`set_normalization_rules`.
        """
        return ElementSnapshot(
            tag=snapshot.tag,
            attributes=self._normalize_attrs(snapshot.attributes),
            text=re.sub(r'\s+', ' ', snapshot.text).strip(),
            parent_tag=snapshot.parent_tag,
            parent_attributes=self._normalize_attrs(snapshot.parent_attributes),
            siblings=[{**s, 'attrs': self._normalize_attrs(s.get('attrs', {}))} for s in snapshot.siblings],
        )

    def _normalize_attrs(self, attrs: dict[str, str]) -> dict[str, str]:
        """Return a new dict with normalization rules applied to *attrs*."""
        result = {}
        for key, value in attrs.items():
            normalized = value
            for attr_name, pattern, replacement in self._normalization_rules:
                if attr_name is not None and key != attr_name:
                    continue

                if replacement is None:
                    # Token-removal mode (for class etc.)
                    tokens = normalized.split()
                    filtered = [t for t in tokens if not pattern.search(t)]
                    if len(filtered) != len(tokens):
                        normalized = ' '.join(filtered)
                elif attr_name is None:
                    # Rule targets attribute name (e.g. data-v-*) —
                    # remove the entire attribute when the key matches
                    if pattern.search(key):
                        normalized = ''
                        break
                elif pattern.search(normalized):
                    # Standard re.sub on value
                    normalized = pattern.sub(replacement, normalized)
                    if not normalized:
                        break

            if normalized:
                result[key] = normalized
        return result

    @abstractmethod
    def save(self, locator_key: str, snapshot: ElementSnapshot) -> None:
        """Persist a snapshot."""

    @abstractmethod
    def load(self, locator_key: str) -> ElementSnapshot | None:
        """Load a previously saved snapshot."""


class JsonFileSnapshotStorage(SnapshotStorage):
    """Stores element snapshots as individual JSON files.

    Each snapshot is written to ``{directory}/{safe_filename}.json``.

    The JSON format is self-describing so that external projects can consume
    these files without any knowledge of MOPS internals::

        {
            "locator_key": "...",
            "snapshot": {
                "tag": "button",
                "attributes": {"id": "submit", ...},
                "text": "Submit",
                "parent_tag": "form",
                "parent_attributes": {"class": "login-form", ...},
                "siblings": [...]
            },
            "updated_at": "2026-05-22T12:00:00+00:00"
        }

    :param directory: Directory path for storing snapshot JSON files.
    """

    def __init__(self, directory: str = '.self_healing_snapshots') -> None:
        super().__init__()
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _key_to_filename(locator_key: str) -> str:
        """Convert a locator key to a safe filesystem name."""
        safe = locator_key.replace('::', '__').replace('/', '_').replace('\\', '_')
        # Limit length to avoid filesystem issues
        if len(safe) > _MAX_FILENAME_LENGTH:
            suffix = hashlib.md5(locator_key.encode(), usedforsecurity=False).hexdigest()[:_FILENAME_HASH_SUFFIX_LENGTH]
            safe = safe[: _MAX_FILENAME_LENGTH - _FILENAME_HASH_SUFFIX_LENGTH - 2] + '__' + suffix
        return safe + '.json'

    def save(self, locator_key: str, snapshot: ElementSnapshot) -> None:
        """Persist a snapshot as a JSON file."""
        filepath = self._directory / self._key_to_filename(locator_key)
        data = {
            'locator_key': locator_key,
            'snapshot': asdict(snapshot),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        with filepath.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, locator_key: str) -> ElementSnapshot | None:
        """Load a snapshot by locator key from its JSON file."""
        filepath = self._directory / self._key_to_filename(locator_key)
        if not filepath.exists():
            return None
        try:
            with filepath.open(encoding='utf-8') as f:
                data = json.load(f)
            return ElementSnapshot(**data['snapshot'])
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return None


class SqliteSnapshotStorage(SnapshotStorage):
    """SQLite-backed storage for element snapshots.

    .. note::
        This class is kept as a reference implementation for developers
        who want to write their own :class:`SnapshotStorage` subclass.
        The default storage is :class:`JsonFileSnapshotStorage`.
    """

    def __init__(self, db_path: str) -> None:
        super().__init__()
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    locator_key TEXT PRIMARY KEY,
                    snapshot_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def save(self, locator_key: str, snapshot: ElementSnapshot) -> None:
        """Persist a snapshot to the SQLite database."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO snapshots (locator_key, snapshot_json, updated_at) VALUES (?, ?, ?)',
                (locator_key, json.dumps(asdict(snapshot)), datetime.now(timezone.utc).isoformat()),
            )
        self._saved_this_session.add(locator_key)

    def load(self, locator_key: str) -> ElementSnapshot | None:
        """Load a snapshot from the SQLite database."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                'SELECT snapshot_json FROM snapshots WHERE locator_key = ?',
                (locator_key,),
            ).fetchone()

        if not row:
            return None

        data = json.loads(row[0])
        return ElementSnapshot(**data)
