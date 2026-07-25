"""Test that Page elements get correct driver-specific methods."""
import inspect

from mops.base.element import Element
from mops.base.page import Page
from mops.selenium.elements.mobile_element import MobileElement
from mops.selenium.elements.web_element import WebElement
from mops.mixins.objects.driver import Driver
from mock.mock import MagicMock
from appium.webdriver.webdriver import WebDriver as AppiumDriver
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumDriver
from mops.base.driver_wrapper import DriverWrapper, DriverWrapperSessions


class Page1(Page):
    element1 = Element('locator1', name='element1')


class Page2(Page):
    element2 = Element('locator2', name='element2')


class MockedDW(DriverWrapper):
    pass


def _assert_method_from(element, name, source_cls):
    raw = inspect.getattr_static(element, name, None)
    assert raw is not None, f"'{name}' not found"
    func = raw.__func__ if isinstance(raw, (classmethod, staticmethod)) else raw
    qualname = getattr(func, '__qualname__', '')
    assert source_cls.__name__ in qualname, (
        f"'{name}' expected from {source_cls.__name__}, got {qualname!r}"
    )


def test_page_elements_different_drivers():
    """Mobile first, then web: last driver type's methods are on the shared class."""
    DriverWrapperSessions.all_sessions = []

    # Mobile driver + page
    appium_driver_cls = AppiumDriver
    appium_driver_cls.__init__ = lambda *a, **kw: None
    appium_driver_cls.session_id = None
    appium_driver_cls.command_executor = MagicMock()
    appium_driver_cls.error_handler = MagicMock()
    appium_driver_cls.capabilities = MagicMock(return_value={
        'platformName': 'ios', 'browserName': 'safari', 'automationName': 'safari'
    })()
    mobile_dw = MockedDW(Driver(driver=appium_driver_cls()))

    page1 = Page1(driver_wrapper=mobile_dw)
    _assert_method_from(page1.element1, 'click_into_center', MobileElement)

    # Web driver + page
    selenium_driver_cls = SeleniumDriver
    selenium_driver_cls.__init__ = lambda *a, **kw: None
    selenium_driver_cls.session_id = None
    selenium_driver_cls.command_executor = MagicMock()
    selenium_driver_cls.error_handler = MagicMock()
    selenium_driver_cls.caps = {}
    web_dw = MockedDW(Driver(driver=selenium_driver_cls()))

    page2 = Page2(driver_wrapper=web_dw)

    _assert_method_from(page2.element2, 'click_into_center', WebElement)
    # Elements share the same class; the last driver (web) sets class-level methods.
    # Instance-level data (locator, name) is per-instance.

    DriverWrapperSessions.all_sessions = []


def test_page_elements_web_first_then_mobile():
    """Web first, then mobile: last driver type's methods are on the shared class."""
    DriverWrapperSessions.all_sessions = []

    # Web driver + page
    selenium_driver_cls = SeleniumDriver
    selenium_driver_cls.__init__ = lambda *a, **kw: None
    selenium_driver_cls.session_id = None
    selenium_driver_cls.command_executor = MagicMock()
    selenium_driver_cls.error_handler = MagicMock()
    selenium_driver_cls.caps = {}
    web_dw = MockedDW(Driver(driver=selenium_driver_cls()))

    page1 = Page1(driver_wrapper=web_dw)
    _assert_method_from(page1.element1, 'click_into_center', WebElement)

    # Mobile driver + page
    appium_driver_cls = AppiumDriver
    appium_driver_cls.__init__ = lambda *a, **kw: None
    appium_driver_cls.session_id = None
    appium_driver_cls.command_executor = MagicMock()
    appium_driver_cls.error_handler = MagicMock()
    appium_driver_cls.capabilities = MagicMock(return_value={
        'platformName': 'ios', 'browserName': 'safari', 'automationName': 'safari'
    })()
    mobile_dw = MockedDW(Driver(driver=appium_driver_cls()))

    page2 = Page2(driver_wrapper=mobile_dw)

    _assert_method_from(page2.element2, 'click_into_center', MobileElement)
    # Elements share the same class; the last driver (mobile) sets class-level methods.

    DriverWrapperSessions.all_sessions = []
