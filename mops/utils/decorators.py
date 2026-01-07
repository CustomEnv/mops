from __future__ import annotations

import time
from functools import wraps
from typing import Callable, Union, Any, TYPE_CHECKING

from mops.exceptions import ContinuousWaitException
from mops.mixins.objects.wait_result import Result
from mops.utils.internal_utils import HALF_WAIT_EL, WAIT_EL, validate_timeout, validate_silent, WAIT_METHODS_DELAY, \
    increase_delay, QUARTER_WAIT_EL
from mops.utils.logs import autolog, LogLevel


if TYPE_CHECKING:
    from mops.base.element import Element


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
                    autolog(
                        f'Caught "{exc.__class__.__name__}" while executing "{func.__name__}", retrying...',
                        level=LogLevel.WARNING
                    )
        return wrapper
    return decorator


def wait_condition(method: Callable):

    @wraps(method)
    def wrapper(
        self: Element,
        *args: Any,
        timeout: Union[int, float] = WAIT_EL,
        silent: bool = False,
        continuous: bool = False,
        **kwargs: Any,
    ):
        validate_timeout(timeout)
        validate_silent(silent)

        should_increase_delay = self.driver_wrapper.is_appium
        delay = WAIT_METHODS_DELAY
        is_log_needed = not silent
        start_time = time.time()

        if continuous:
            return method(self, *args, **kwargs)

        while time.time() - start_time < timeout:
            result: Result = method(self, *args, **kwargs)

            if is_log_needed:
                self.log(result.log)
                is_log_needed = False

            if result.execution_result:
                return self

            time.sleep(delay)

            if should_increase_delay:
                delay = increase_delay(delay)

        result.exc._timeout = timeout  # noqa
        raise result.exc

    return wrapper


def wait_continuous(method: Callable):

    @wraps(method)
    def wrapper(
        self: Element,
        *args: Any,
        silent: bool = False,
        continuous: Union[int, float, bool] = False,
        **kwargs: Any
    ):
        result: Element = method(self, *args, silent=silent, continuous=False, **kwargs)  # Wait for initial condition

        if not continuous:
            return result

        should_increase_delay = self.driver_wrapper.is_appium
        delay = WAIT_METHODS_DELAY
        start_time = time.time()
        is_log_needed = not silent
        timeout = continuous if type(continuous) in (int, float) else QUARTER_WAIT_EL

        while time.time() - start_time < timeout:
            result: Result = method(self, *args, silent=silent, continuous=True, **kwargs)

            if is_log_needed:
                self.log(f'Starting continuous "{method.__name__}" for the "{self.name}" for next {timeout} seconds')
                is_log_needed = False

            if not result.execution_result:
                raise ContinuousWaitException(
                    f'The continuous "{method.__name__}" of the "{self.name}" is no met ' 
                    f'after {(time.time() - start_time):.2f} seconds'
                )

            time.sleep(delay)

            if should_increase_delay:
                delay = increase_delay(delay)

        return self

    return wrapper
