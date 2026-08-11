"""Utilities for self-healing tests."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from collections.abc import Iterator


@contextmanager
def spy_healing(cls: type) -> Iterator[dict]:
    """Spy on ``cls._attempt_healing`` calls.

    Usage::

        with spy_healing(CoreElement) as spy:
            element.some_action()

        assert not spy['called']
        assert 'SomeElement' not in spy['instances']
    """
    state: dict = {'called': False, 'instances': []}
    original = cls._attempt_healing

    def _spy(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
        state['called'] = True
        state['instances'].append(self.name)
        return original(self, *args, **kwargs)

    with patch.object(cls, '_attempt_healing', _spy):
        yield state
