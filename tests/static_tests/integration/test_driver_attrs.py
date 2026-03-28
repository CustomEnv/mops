import inspect

from mops.base.driver_wrapper import DriverWrapper
from mops.playwright.play_driver import PlayDriver
from mops.selenium.core.core_driver import CoreDriver
from mops.selenium.driver.mobile_driver import MobileDriver
from mops.selenium.driver.web_driver import WebDriver
from mops.utils.internal_utils import get_attributes_from_object


def _own_methods(cls):
    return {
        name for name, val in get_attributes_from_object(cls).items()
        if not name.startswith('_') and callable(val)
    }


def _assert_from(dw, methods, source_cls):
    for name in methods:
        raw = inspect.getattr_static(dw, name, None)
        assert raw is not None, f"'{name}' not found on {type(dw).__name__}"
        func = raw.__func__ if isinstance(raw, (classmethod, staticmethod)) else raw
        qualname = getattr(func, '__qualname__', '')
        assert source_cls.__name__ in qualname, (
            f"'{name}' on {type(dw).__name__} expected from {source_cls.__name__}, "
            f"got {qualname!r}"
        )


_WRAPPER = _own_methods(DriverWrapper)
_WEB = _own_methods(WebDriver)
_MOBILE = _own_methods(MobileDriver)
_CORE = _own_methods(CoreDriver)
_PLAY = _own_methods(PlayDriver)


def _assert_android_attrs(dw):
    _assert_from(dw, _MOBILE, MobileDriver)
    _assert_from(dw, _CORE - _MOBILE - _WRAPPER, CoreDriver)
    _assert_from(dw, _WRAPPER, DriverWrapper)


def _assert_selenium_attrs(dw):
    _assert_from(dw, _WEB, WebDriver)
    _assert_from(dw, _CORE - _WEB - _WRAPPER, CoreDriver)
    _assert_from(dw, _WRAPPER, DriverWrapper)


def _assert_playwright_attrs(dw):
    _assert_from(dw, _PLAY - _WRAPPER, PlayDriver)
    _assert_from(dw, _WRAPPER, DriverWrapper)


def test_android_and_selenium_attrs(mocked_android_driver, mocked_selenium_driver):
    assert 'Shadow' not in type(mocked_android_driver).__name__
    assert type(mocked_selenium_driver).__name__ == 'ShadowDriverWrapper'
    _assert_android_attrs(mocked_android_driver)
    _assert_selenium_attrs(mocked_selenium_driver)


def test_android_and_playwright_attrs(mocked_android_driver, mocked_play_driver):
    assert 'Shadow' not in type(mocked_android_driver).__name__
    assert type(mocked_play_driver).__name__ == 'ShadowDriverWrapper'
    _assert_android_attrs(mocked_android_driver)
    _assert_playwright_attrs(mocked_play_driver)
