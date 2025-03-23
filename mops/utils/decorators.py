from __future__ import annotations

import time
from functools import wraps
from typing import Callable, Union

from mops.mixins.objects.wait_result import Result
from mops.utils.internal_utils import HALF_WAIT_EL, WAIT_EL, validate_timeout, validate_silent, WAIT_METHODS_DELAY, \
    increase_delay
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


def wait_condition(method: Callable):

    @wraps(method)
    def wrapper(self, *args, timeout: Union[int, float] = WAIT_EL, silent: bool = False, **kwargs):
        validate_timeout(timeout)
        validate_silent(silent)

        start_time = time.time()
        result: Result = method(self, *args, **kwargs)

        if not silent:
            self.log(result.log)

        should_increase_delay = self.driver_wrapper.is_appium
        delay = WAIT_METHODS_DELAY

        while time.time() - start_time < timeout:
            result: Result = method(self, *args, **kwargs)

            if result.execution_result:
                return self

            time.sleep(delay)

            if should_increase_delay:
                delay = increase_delay(delay)

        result.exc._timeout = timeout  # noqa
        raise result.exc

    return wrapper
