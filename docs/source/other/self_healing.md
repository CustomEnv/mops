# Self-Healing Locators

## Overview

Self-healing locators automatically recover broken element locators at runtime.
When an element is successfully located, its DOM context (tag, attributes, text, parent, siblings) is saved as a snapshot.
If the original locator later fails, the system scans all elements with the same tag on the page,
finds the most similar one, generates new stable locators, and updates the element transparently.

Supported for both **Selenium** and **Playwright** backends.

```{attention}
Snapshots are saved per unique locator key per session. If a page changes significantly between runs,
the snapshot should be refreshed by calling `wait_visibility()` or any other element-interaction method
that triggers snapshot saving.
```

<br>

## Quick Start

```python
from mops.self_healing import configure, JsonFileSnapshotStorage

# Minimal setup — save snapshots and heal broken locators
configure(
    save_snapshots=True,
    heal_locators=True,
    storage=JsonFileSnapshotStorage('snapshots'),
)

# Use elements normally — snapshots are saved automatically on first successful lookup
my_element = page.my_button
my_element.click()  # snapshot saved here

# If the locator breaks (e.g., after a deploy), healing kicks in transparently
my_element.click()  # heals automatically
```

<br>

## Configuration

```{eval-rst}
.. autoclass:: mops.self_healing.config.SelfHealingConfig
   :members:
   :undoc-members:
```

### Storage Backends

**`JsonFileSnapshotStorage`** (default) — stores each snapshot as a JSON file on disk:

```python
from mops.self_healing import JsonFileSnapshotStorage

configure(storage=JsonFileSnapshotStorage('my_snapshots'))
```

**Custom backends** — implement `SnapshotStorage` ABC:

```python
from mops.self_healing.snapshot import SnapshotStorage, ElementSnapshot

class MyRedisStorage(SnapshotStorage):
    def save(self, locator_key, snapshot):
        ...

    def load(self, locator_key):
        ...
```

### Callbacks

```python
def on_success(result):
    # result.healed_locator — the new working locator
    # result.score — similarity score (0-1)
    # result.original_locator — the broken locator
    # result.timestamp — when the heal happened (ISO-8601, UTC)
    # result.breakdown — SimilarityBreakdown of the best candidate
    metrics.increment('healing.success', tags={'element': result.element_name})

def on_failure(result):
    # result.reason — 'no-snapshot', 'below-threshold', 'no-verified-locator'
    # result.locator — the broken locator
    # result.best_score — highest similarity score found before failure
    #                     (0-1), or None if no candidate could be scored
    # result.score_threshold — the configured acceptance threshold
    # result.candidates_count — how many DOM candidates were compared
    # result.breakdown — SimilarityBreakdown of the best candidate, or None
    alerting.send(f'Healing failed for {result.element_name}: {result.reason} (best score: {result.best_score})')

configure(
    save_snapshots=True,
    heal_locators=True,
    storage=JsonFileSnapshotStorage(),
    on_healing_success=on_success,
    on_healing_failure=on_failure,
)
```

Both callbacks receive a `SimilarityBreakdown` in `result.breakdown` for the **best candidate** —
regardless of whether healing succeeded or failed. It tells you exactly which attributes
matched the snapshot and which did not:

```python
def on_healing_result(result):
    b = result.breakdown
    print(f'matched: {b.matched_attributes}')        # ['id', 'name']
    print(f'mismatched: {b.mismatched_attributes}')  # ['class']

    # Inspect a specific attribute to spot dynamic data
    id_match = b.attributes['id']
    print(id_match.snapshot_value, '->', id_match.candidate_value)  # 'user-123' -> 'user-456'
    print(id_match.matched, id_match.score)  # False 0.0

    # The raw DOM snapshot of the best candidate as found on the page
    snap = b.candidate_snapshot
    print(snap.attributes, snap.text, snap.parent_tag)
```

* `AttributeMatch` — one per attribute: `attribute`, `snapshot_value`, `candidate_value`,
  `matched`, `score` (0-1), `weight` (0.0 for attributes that do not affect scoring).
* `SimilarityBreakdown` — `score`, `attributes` (dict), `text_snapshot`, `text_candidate`,
  `text_score`, `parent_tag_*`, `parent_attrs_score`, `siblings_score`,
  `siblings_snapshot_count`, `siblings_candidate_count`, `candidate_snapshot`
  (a raw `ElementSnapshot` of the best candidate — reflects the actual DOM state,
  unlike the normalized reference stored in the storage), plus convenience
  `matched_attributes` / `mismatched_attributes` lists.

### Scoring Weights

Tune similarity scoring per attribute type — externally, from any project that
uses the framework. Pass your own `ScoringWeights` through `configure()`:

```python
from mops.self_healing import configure, ScoringWeights, JsonFileSnapshotStorage

configure(
    save_snapshots=True,
    heal_locators=True,
    storage=JsonFileSnapshotStorage(),
    scoring_weights=ScoringWeights(
        attribute={'id': 1.0, 'class': 0.3, 'name': 0.7},
        text=0.5,
        parent=0.2,
        siblings=0.1,
    ),
)
```

`attribute` maps an attribute name to its weight; keys not present are ignored
during scoring (weight `0.0`). Weights apply to every element globally. Changing
them at runtime is picked up on the next heal: the `Healer` singleton
re-initialises when `scoring_weights`, `score_threshold`, `storage`, or
`on_healing_failure` change. Mutating the same `ScoringWeights` object in place
(e.g. `get_config().scoring_weights.attribute['id'] = 0.9`) also works because
the `Healer` keeps a reference to it.

### Healing Statistics

Process-wide counters for end-of-run reporting (e.g. in `pytest_sessionfinish`):

```python
from mops.self_healing import get_healing_stats

def pytest_sessionfinish(session, exitstatus):
    stats = get_healing_stats()
    print(f'healing: {stats.healed} ok, {stats.failed} failed of {stats.attempts}')
    print(f'average best score: {stats.avg_best_score}')
    print(f'failure reasons: {stats.failed_reasons}')
```

`HealingStats` fields: `attempts`, `healed`, `failed`, `failed_reasons` (per-reason breakdown),
and `avg_best_score` (average similarity of successful heals).
Note that `healed` counts candidates found by the Healer — a candidate can still fail DOM
verification afterwards (`no-verified-locator`), which is reported via `on_healing_failure`
but not counted here.

### Snapshot Normalization

Remove dynamic data (CSS hashes, state classes) from snapshots before saving:

```python
import re

storage = JsonFileSnapshotStorage()
storage.set_normalization_rules([
    *storage._normalization_rules,          # keep defaults
    ('data-track', re.compile(r'.*'), ''),  # remove data-track entirely
    (None, re.compile(r'-\d+'), ''),        # strip numeric suffixes from any attr
])
```

<br>

## Architecture

### Decorators

```{eval-rst}
.. autofunction:: mops.utils.decorators.healing
.. autofunction:: mops.utils.decorators.healing_after_wait
.. autofunction:: mops.utils.decorators.no_healing
```

**`@healing`** — applied on action methods (`click`, `type_text`, `get_attribute`, etc.).
Catches `NoSuchElementException`, attempts healing, retries the method once with the healed locator.

**`@healing_after_wait`** — applied on `wait_visibility` and `wait_availability`.
Triggers healing after the wait condition times out.

**`@no_healing`** — applied on methods that must never trigger healing (`is_displayed`, `wait_hidden`).
Temporarily disables `heal_locators` on the global config.

### Healing Flow

1. **Snapshot capture** — on first successful element lookup, DOM context is extracted via JS and saved to storage.
   The storage key is the element's hierarchical locator key (`name::locator -> parent::locator`).

2. **Healing trigger** — when an action method raises `NoSuchElementException`, `@healing` catches it,
   or when `@healing_after_wait` catches a wait timeout.

3. **Candidate search** — JS script collects all elements with the same tag, extracts their attributes,
   text, parent, and up to 5 siblings.

4. **Similarity scoring** — each candidate is scored against the saved snapshot.
   Attributes (`id`, `name`, `class`, `aria-label`, etc.) have per-key weights.
   Text, parent tag/attributes, and sibling structure contribute additional weighted scores.
   The best candidate must exceed `score_threshold` (default `0.7`).

5. **Locator generation** — stable XPath locators are generated for the best candidate:
   `@id` → `data-testid` → `@name` → `@aria-label` → `@type` → stable `@class` → visible text → positional XPath.
   The caller tries each in order until one resolves.

6. **Locator persistence** — the first working locator is written to the element's `locator` attribute.
   Subsequent lookups use the healed locator directly.

### Key Classes

```{eval-rst}
.. autoclass:: mops.self_healing.healer.Healer
   :members: heal
   :undoc-members:

.. autoclass:: mops.self_healing.healer.SuccessHealingResult
   :members:
   :undoc-members:

.. autoclass:: mops.self_healing.healer.FailedHealingResult
   :members:
   :undoc-members:

.. autoclass:: mops.self_healing.snapshot.SnapshotStorage
   :members: save, load, save_from_element, extract_full_locator_key, set_normalization_rules
   :undoc-members:

.. autoclass:: mops.self_healing.snapshot.ElementSnapshot
   :members:
   :undoc-members:

.. autoclass:: mops.self_healing.snapshot.JsonFileSnapshotStorage
   :members:
   :undoc-members:

.. autoclass:: mops.self_healing.healer.ScoringWeights
   :members:
   :undoc-members:

.. autoclass:: mops.self_healing.healer.AttributeMatch
   :members:
   :undoc-members:

.. autoclass:: mops.self_healing.healer.SimilarityBreakdown
   :members:
   :undoc-members:

.. autoclass:: mops.self_healing.healer.HealingStats
   :members:
   :undoc-members:

.. autofunction:: mops.self_healing.healer.get_healing_stats
```

<br>

## Disabling Healing

### Per-method: `@no_healing`

```python
from mops.utils.decorators import no_healing

class MyElement(Element):
    @no_healing
    def is_displayed(self, silent=False):
        ...
```

### Globally

```python
from mops.self_healing import configure

# Save snapshots but don't heal (data collection mode)
configure(save_snapshots=True, heal_locators=False)

# Disable entirely
configure(save_snapshots=False, heal_locators=False)
```

<br>

## Error Handling

Healing failures are non-fatal — the original exception is re-raised if healing cannot find a working locator.

| Phase | Failure Reason | Callback |
|-------|---------------|----------|
| No snapshot saved | `no-snapshot` | `on_healing_failure` |
| JS script error | `candidates-script-error` | `on_healing_failure` |
| No matching candidates on page | `no-candidates` | `on_healing_failure` |
| Best score below threshold | `below-threshold` | `on_healing_failure` |
| Best index out of bounds | `index-out-of-bounds` | `on_healing_failure` |
| Locator generation error | `generate-locator-error` | `on_healing_failure` |
| No candidate passes DOM verification | `no-verified-locator` | `on_healing_failure` |
| Candidate passes DOM verification | — | `on_healing_success` |

`FailedHealingResult` exposes diagnostics for external monitoring
(`SuccessHealingResult` also carries a `timestamp`):

* `best_score` — highest similarity score found before the failure
  (`below-threshold`, `index-out-of-bounds`, `generate-locator-error`, `no-verified-locator`),
  or `None` when no candidate could be scored (`no-snapshot`, `candidates-script-error`, `no-candidates`).
* `score_threshold` — the configured acceptance threshold.
* `candidates_count` — how many DOM candidates were compared, or `None` when candidates were never collected.
* `breakdown` — a `SimilarityBreakdown` of the best candidate whenever one was scored
  (`below-threshold`, `index-out-of-bounds`, `generate-locator-error`, `no-verified-locator`),
  or `None` when no candidate could be scored. The same breakdown is available on
  `SuccessHealingResult` after a successful heal.

<br>

## Methods with Healing

| Method | `@healing` | `@healing_after_wait` |
|--------|-----------|----------------------|
| `click` | ✓ | |
| `type_text` | ✓ | |
| `type_slowly` | ✓ | |
| `clear_text` | ✓ | |
| `check` | ✓ | |
| `uncheck` | ✓ | |
| `hover` | ✓ | |
| `get_attribute` | ✓ | |
| `is_enabled` | ✓ | |
| `is_checked` | ✓ | |
| `screenshot_image` | ✓ | |
| `screenshot_base` | ✓ | |
| `text` | ✓ | |
| `inner_text` | ✓ | |
| `value` | ✓ | |
| `scroll_into_view` | ✓ | |
| `hide` | ✓ | |
| `show` | ✓ | |
| `wait_visibility` | | ✓ |
| `wait_availability` | | ✓ |

Methods without these decorators (`is_displayed`, `is_available`, `is_hidden`, `wait_hidden`, `wait_hidden_without_error`) do not trigger healing.
