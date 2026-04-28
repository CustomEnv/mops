from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import sqlite3
from typing import Any


@dataclass
class ElementSnapshot:
    """Snapshot of a successfully located element's DOM context."""

    tag: str
    attributes: dict[str, str]
    text: str
    parent_tag: str | None
    parent_attributes: dict[str, str]
    siblings: list[dict[str, Any]]


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


class SnapshotStorage:
    """SQLite-backed storage for element snapshots."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._saved_this_session: set[str] = set()
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

    def save_from_element(self, locator_key: str, web_element: object, driver: object) -> None:
        """Extract snapshot from a live web element and persist it."""
        if locator_key in self._saved_this_session:
            return

        try:
            raw = driver.execute_script(_GET_ELEMENT_SNAPSHOT_JS, web_element)
        except Exception:
            return

        snapshot = ElementSnapshot(
            tag=raw['tag'],
            attributes=raw['attrs'],
            text=raw['text'],
            parent_tag=raw['parentTag'],
            parent_attributes=raw['parentAttrs'],
            siblings=raw['siblings'],
        )

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO snapshots (locator_key, snapshot_json, updated_at) VALUES (?, ?, ?)',
                (locator_key, json.dumps(asdict(snapshot)), datetime.now(timezone.utc).isoformat()),
            )

        self._saved_this_session.add(locator_key)

    def save(self, locator_key: str, snapshot: ElementSnapshot) -> None:
        """Persist a snapshot directly without a live web element."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO snapshots (locator_key, snapshot_json, updated_at) VALUES (?, ?, ?)',
                (locator_key, json.dumps(asdict(snapshot)), datetime.now(timezone.utc).isoformat()),
            )
        self._saved_this_session.add(locator_key)

    def load(self, locator_key: str) -> ElementSnapshot | None:
        """Load a previously saved snapshot for the given locator key."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                'SELECT snapshot_json FROM snapshots WHERE locator_key = ?',
                (locator_key,),
            ).fetchone()

        if not row:
            return None

        data = json.loads(row[0])
        return ElementSnapshot(**data)
