import time
from types import SimpleNamespace
from typing import Union
from unittest.mock import patch

import pytest
from mops.exceptions import TimeoutException
from mops.utils.internal_utils import WAIT_METHODS_DELAY
from mops.utils.decorators import healing_after_wait, wait_condition
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
    """ sleep for 0.1, 0.2, 0.4 seconds between iterations """
    namespace = MockNamespace('wait some condition', call_count=3, is_mobile=True)
    start_time = time.time()
    namespace.wait_something()
    end_time = time.time() - start_time
    assert end_time > 0.7
    print(end_time)
    assert end_time < 0.75


# ---------------------------------------------------------------------------
# Healing-after-wait tests
# ---------------------------------------------------------------------------


class MockHealableNamespace(MockNamespace):
    """Like MockNamespace but supports _heal_after_wait for wait_condition healing."""

    def __init__(self, log_msg: str, call_count: int, heal_after_wait_result: bool = False, **kwargs):
        super().__init__(log_msg, call_count, **kwargs)
        self._heal_after_wait_result = heal_after_wait_result
        self.heal_after_wait_called = False
        self._post_heal_retry = False

    def get_result(self):
        # After healing, the retry call should always succeed
        if self._post_heal_retry:
            return True
        return super().get_result()

    def _heal_after_wait(self) -> bool:
        self.heal_after_wait_called = True
        if self._heal_after_wait_result:
            self._post_heal_retry = True
        return self._heal_after_wait_result

    @healing_after_wait
    @wait_condition
    def wait_something(self, *, timeout: Union[int, float] = 1, silent: bool = False) -> bool:  # noqa
        return Result(  # noqa
            execution_result=self.get_result(),
            log=self.log_msg,
            exc=TimeoutException('wait some condition failed!'),
        )


def test_wait_condition_heal_on_timeout_called():
    """After wait times out, _heal_after_wait is called."""
    namespace = MockHealableNamespace('wait', call_count=10, heal_after_wait_result=False)

    with patch('mops.utils.decorators.get_config') as mock_cfg:
        mock_cfg.return_value.heal_locators = True
        with pytest.raises(TimeoutException):
            namespace.wait_something(timeout=0.1)

    assert namespace.heal_after_wait_called


def test_wait_condition_heal_success_retries():
    """_heal_after_wait returns True -> wait is retried and succeeds."""
    namespace = MockHealableNamespace('wait', call_count=10, heal_after_wait_result=True)

    with patch('mops.utils.decorators.get_config') as mock_cfg:
        mock_cfg.return_value.heal_locators = True
        result = namespace.wait_something(timeout=0.1)

    assert result is namespace
    assert namespace.heal_after_wait_called


def test_wait_condition_heal_fails_raises():
    """_heal_after_wait returns False -> original exception raised."""
    namespace = MockHealableNamespace('wait', call_count=10, heal_after_wait_result=False)

    with patch('mops.utils.decorators.get_config') as mock_cfg:
        mock_cfg.return_value.heal_locators = True
        with pytest.raises(TimeoutException) as exc_info:
            namespace.wait_something(timeout=0.1)

    assert 'wait some condition failed!' in str(exc_info.value)
    assert namespace.heal_after_wait_called


def test_wait_condition_no_heal_method():
    """Element without _heal_after_wait -> no healing, original exception."""
    namespace = MockNamespace('wait', call_count=10)

    with pytest.raises(TimeoutException):
        namespace.wait_something(timeout=0.1)


def test_wait_condition_heal_retry_also_times_out():
    """If the retry after healing also fails, original exception is raised."""
    namespace = MockHealableNamespace('wait', call_count=10, heal_after_wait_result=True)
    # After _heal_after_wait, the retry gets result from get_result().
    # Since _post_heal_retry is True, get_result() returns True.
    # To test retry failure, override the retry behavior.
    original_heal = namespace._heal_after_wait

    def heal_and_no_retry():
        original_heal()
        namespace._post_heal_retry = False  # undo the retry-success flag
        return True

    namespace._heal_after_wait = heal_and_no_retry

    with pytest.raises(TimeoutException):
        namespace.wait_something(timeout=0.1)

def test_wait_condition_desktop_default_delay():
    """ sleep for 0.1 seconds between iterations """
    namespace = MockNamespace('wait some condition', call_count=3, is_mobile=False)
    start_time = time.time()
    namespace.wait_something()
    end_time = time.time() - start_time
    assert end_time > 0.7
    print(end_time)
    assert end_time < 0.75
