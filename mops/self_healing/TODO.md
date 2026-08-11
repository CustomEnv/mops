# Self-Healing TODO

Backlog of not-yet-implemented improvements for the self-healing feature.

## 1. Multiple ancestors comparison (P4)

**Status:** not implemented

**Problem:** scoring compares only the immediate DOM parent. When a new wrapper
(e.g. a React `InputContainer__childrenWrapper`) is inserted, the old snapshot's
parent context (e.g. `parent-studios-add-modal` modal container) is no longer
the direct parent, and the parent similarity drops.

**Goal:** compare several ancestors up the DOM and accept a candidate if its
ancestor chain contains a matching container (e.g. the modal), even when an
intermediate wrapper was added.

**What it touches:**
- JS: `_GET_CANDIDATES_JS` / `_GET_ELEMENT_SNAPSHOT_JS` — collect an ancestor
  chain (3–5 levels) instead of only the immediate parent
- `ElementSnapshot` + snapshot JSON storage format — new `ancestors` field
  (keep backward compatibility with old snapshots)
- `_score_similarity` — match each snapshot ancestor against the candidate's
  ancestor chain ("search for the modal container anywhere in the chain")
- Breakdown: expose ancestor-level scores

**Reference case (currently passing via P1–P3, would be made robust):**
`input` inside a modal (`parent-studios-add-modal`) got wrapped by
`InputContainer__childrenWrapper` — placeholder anchor + HTML defaults + optional
siblings push the score above threshold, but the immediate-parent signal is lost.

## 2. DOM index drift guard (temporarily removed)

**Status:** removed, tests stubbed out in
`tests/static_tests/unit/test_self_healing_scoring.py`

**Problem:** the resolved element at `best_index` may no longer match the best
candidate if the DOM changed between the candidates JS scan and `find_elements`
(React re-renders).

**Re-add:** re-snapshot the resolved element and compare with the best candidate;
on mismatch fail with a `dom-changed-during-healing` reason.

## 3. Placeholder-aware text matching (P2)

**Status:** not implemented

**Problem:** `{username}` in a snapshot text never matches a real value
(`m_john_456`), and naive "normalize any text to `{username}`" risks merging
distinct elements.

**Goal:** per-placeholder matchers with regex patterns (`{username}`, `{id}`,
`{date}`, `{token}`); `snapshot_text == '{username}'` should match only values
that fit the username pattern, and ideally work for partial templates too
(`"User: {username}"`).
