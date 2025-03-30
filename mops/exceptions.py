from typing import Any


class DriverWrapperException(Exception):
    """Base driver wrapper exceptions."""

    def __init__(
            self,
            msg: str,
            actual: Any = None,
            expected: Any = None,
            timeout: Any = None,
            info: Any = None,
    ):
        self._msg = ''
        self._original_msg = msg
        self._timeout = timeout
        self._actual = actual
        self._expected = expected
        self._info = info
        self.__suppress_context__ = True

    def __str__(self) -> str:
        return f'\nMessage: {self.msg}'

    @property
    def msg(self):
        self._msg = f'{self._original_msg} '

        if self._timeout:
            self._msg += f'after {self._timeout} seconds. '
        if self._expected is not None:
            self._msg += f'Actual: {self.wrap_by_quotes(self._actual)}; ' \
                         f'Expected: {self.wrap_by_quotes(self._expected)}. '
        if self._info:
            self._msg += f'{self._info.get_element_info()}. '

        return self._msg.rstrip()

    def wrap_by_quotes(self, data):
        if data is None:
            data = ''

        if isinstance(data, str):
            return f'"{data}"'

        return data


class UnexpectedElementsCountException(DriverWrapperException):
    """Thrown when elements count isn't equal to expected."""


class UnexpectedElementSizeException(DriverWrapperException):
    """Thrown when element size isn't equal to expected."""


class UnexpectedValueException(DriverWrapperException):
    """Thrown when element contains incorrect value."""


class UnexpectedTextException(DriverWrapperException):
    """Thrown when element contains incorrect text."""


class TimeoutException(DriverWrapperException):
    """Thrown when timeout exceeded."""


class InvalidSelectorException(DriverWrapperException):
    """Thrown when element have invalid selector."""


class NoSuchElementException(DriverWrapperException):
    """Thrown when element could not be found."""


class NoSuchParentException(DriverWrapperException):
    """Thrown when parent could not be found."""


class ElementNotInteractableException(DriverWrapperException):
    """Thrown when element found and enabled but not interactable."""


class UnsuitableArgumentsException(DriverWrapperException):
    """Thrown when object initialised with unsuitable arguments."""


class NotInitializedException(DriverWrapperException):
    """Thrown when getting access to not initialized object."""


class InvalidLocatorException(DriverWrapperException):
    """Thrown when locator is invalid."""


class ContinuousWaitException(DriverWrapperException):
    """Thrown when continuous wait is failed."""


class VisualComparisonException(DriverWrapperException):
    """Thrown when visual comparison error occur."""
