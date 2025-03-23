from __future__ import annotations

import time
from functools import wraps

from mops.utils.internal_utils import HALF_WAIT_EL
from mops.utils.logs import autolog, LogLevel


def retry(exceptions, timeout: int = HALF_WAIT_EL):
    """
    A decorator to retry a function when specified exceptions occur.

    :param exceptions: Exception or tuple of exception classes to catch and retry on.
    :param timeout: The maximum time (in seconds) to keep retrying before giving up.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = None

            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if not timestamp:
                        timestamp = time.time()
                    elif time.time() - timestamp >= timeout:
                        raise exc
                    autolog(f'Caught {exc.__class__.__name__}, retrying...', level=LogLevel.WARNING)
        return wrapper
    return decorator
