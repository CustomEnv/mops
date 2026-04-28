from __future__ import annotations

from functools import wraps
import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

_ctx = threading.local()


def no_healing(func: Callable) -> Callable:
    """Decorator that disables self-healing for the duration of the wrapped method.

    Use on methods where element not being found is an acceptable outcome,
    e.g. is_displayed(), is_hidden(), wait_hidden().
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _ctx.enabled = False
        try:
            return func(*args, **kwargs)
        finally:
            _ctx.enabled = True

    return wrapper


def is_healing_enabled() -> bool:
    """Return True if healing is allowed in the current thread context."""
    return getattr(_ctx, 'enabled', True)
