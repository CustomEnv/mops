import time
from types import SimpleNamespace
from typing import Union

import pytest
from mops.exceptions import TimeoutException
from mops.utils.internal_utils import WAIT_METHODS_DELAY
from mops.utils.decorators import wait_condition
from mops.utils.logs import autolog
from mops.mixins.objects.wait_result import Result


namespace_default_cals_count = 3


class MockNamespace:

    def __init__(self, log_msg: str, call_count: int, is_mobile: bool = False):
        self.call_count = call_count
        self.actual_call_count = 0
        self.log_msg = log_msg
        self.driver_wrapper = SimpleNamespace()
        self.driver_wrapper.is_appium = is_mobile

    def log(self, *args, **kwargs):
        return autolog(*args, **kwargs)

    def get_result(self):
        if self.actual_call_count == self.call_count:
            return True

        self.actual_call_count += 1

        return False

    @wait_condition
    def wait_something(self, *, timeout: Union[int, float] = 1, silent: bool = False) -> bool:  # noqa
        return Result(  # noqa
            execution_result=self.get_result(),
            log=self.log_msg,
            exc=TimeoutException('wait some condition failed!'),
        )


@pytest.mark.parametrize('call_count', [0, 3], ids=['initial pass', 'pass after 3 retries'])
def test_wait_condition_positive(caplog, call_count):
    namespace = MockNamespace('wait some condition', call_count=call_count)
    start_time = time.time()
    result = namespace.wait_something()
    execution_time = time.time() - start_time
    assert execution_time < WAIT_METHODS_DELAY * call_count or 1, \
        'delay inside wait_condition decorator unexpectedly executed for initially passed wait'
    assert result == namespace, 'wait condition method does not return the `self` object'
    assert caplog.messages.count(namespace.log_msg) == 1, 'log message throttled'


def test_wait_condition_negative_with_wait(caplog):
    call_count = 5
    timeout = call_count / 110
    namespace = MockNamespace('wait some condition', call_count=call_count)
    start_time = time.time()

    try:
        namespace.wait_something(timeout=timeout)
    except TimeoutException as exc:
        assert exc.msg == f'wait some condition failed! after {timeout} seconds.'
    else:
        raise Exception('Unexpected behaviour')

    execution_time = time.time() - start_time

    assert timeout < WAIT_METHODS_DELAY * call_count, 'negative case not covered'
    assert execution_time < WAIT_METHODS_DELAY * call_count,\
        'wait_something execution time for negative check somehow higher that given timeout'
    assert caplog.messages.count(namespace.log_msg) == 1, 'log message throttled'


def test_wait_condition_silent(caplog):
    namespace = MockNamespace('wait some condition', call_count=2)
    namespace.wait_something(silent=True)
    assert caplog.messages == [], 'unexpected log messages found'


def test_wait_condition_non_named_arg():
    namespace = MockNamespace('wait some condition', call_count=1)
    try:
        namespace.wait_something(1)
    except TypeError as exc:
        assert 'wait_something() takes 1 positional argument but 2 were given' in str(exc)
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.parametrize('timeout', [True, False], ids=['timeout=True', 'timeout=False'])
def test_wait_condition_timeout_unexpected_bool_value(timeout):
    namespace = MockNamespace('wait some condition', call_count=1)
    try:
        namespace.wait_something(timeout=timeout)
    except TypeError as exc:
        assert "The type of `timeout` arg must be int or float" in str(exc)
    else:
        raise Exception('Unexpected behavior')


@pytest.mark.parametrize('timeout', [0, -1], ids=['timeout=0', 'timeout=-1'])
def test_wait_condition_timeout_unexpected_negative_value(timeout):
    namespace = MockNamespace('wait some condition', call_count=1)
    try:
        namespace.wait_something(timeout=timeout)
    except ValueError as exc:
        assert "The `timeout` value must be a positive number" in str(exc)
    else:
        raise Exception('Unexpected behavior')



@pytest.mark.parametrize('silent', [1, None], ids=['silent=1', 'silent=None'])
def test_wait_condition_silent_unexpected_value(silent):
    namespace = MockNamespace('wait some condition', call_count=1)
    try:
        namespace.wait_something(silent=silent)  # noqa
    except TypeError as exc:
        assert f"The type of `silent` arg must be bool" in str(exc)
    else:
        raise Exception('Unexpected behavior')


def test_wait_condition_mobile_delay_increasing():
    namespace = MockNamespace('wait some condition', call_count=4, is_mobile=True)
    start_time = time.time()
    namespace.wait_something()
    end_time = time.time() - start_time
    assert end_time > 0.7
    assert end_time < 0.8



def test_wait_condition_desktop_default_delay():
    namespace = MockNamespace('wait some condition', call_count=6, is_mobile=False)
    start_time = time.time()
    namespace.wait_something()
    end_time = time.time() - start_time
    assert end_time < 0.6
    assert end_time > 0.5