"""Test that each driver type gets its own Element subclass in multi-driver mode."""
import inspect

from mops.base.element import Element
from mops.selenium.elements.mobile_element import MobileElement
from mops.selenium.elements.web_element import WebElement
from mops.mixins.objects.driver import Driver
from mock.mock import MagicMock
from appium.webdriver.webdriver import WebDriver as AppiumDriver
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumDriver
from mops.base.driver_wrapper import DriverWrapper, DriverWrapperSessions


def _assert_method_from(element, name, source_cls):
    raw = inspect.getattr_static(element, name, None)
    assert raw is not None, f"'{name}' not found"
    func = raw.__func__ if isinstance(raw, (classmethod, staticmethod)) else raw
    qualname = getattr(func, '__qualname__', '')
    assert source_cls.__name__ in qualname, (
        f"'{name}' expected from {source_cls.__name__}, got {qualname!r}"
    )


class MockedDW(DriverWrapper):
    pass


def test_elements_get_own_driver_methods():
    """Elements from the last driver type set the class-level methods."""
    DriverWrapperSessions.all_sessions = []

    # Mobile driver + element
    appium_driver_cls = AppiumDriver
    appium_driver_cls.__init__ = lambda *a, **kw: None
    appium_driver_cls.session_id = None
    appium_driver_cls.command_executor = MagicMock()
    appium_driver_cls.error_handler = MagicMock()
    appium_driver_cls.capabilities = MagicMock(return_value={
        'platformName': 'ios', 'browserName': 'safari', 'automationName': 'safari'
    })()
    mobile_dw = MockedDW(Driver(driver=appium_driver_cls()))

    el_mobile = Element('m1', driver_wrapper=mobile_dw)
    _assert_method_from(el_mobile, 'click_into_center', MobileElement)

    # Web driver + element
    selenium_driver_cls = SeleniumDriver
    selenium_driver_cls.__init__ = lambda *a, **kw: None
    selenium_driver_cls.session_id = None
    selenium_driver_cls.command_executor = MagicMock()
    selenium_driver_cls.error_handler = MagicMock()
    selenium_driver_cls.caps = {}
    web_dw = MockedDW(Driver(driver=selenium_driver_cls()))

    el_web = Element('w1', driver_wrapper=web_dw)

    # Each driver type gets its own cached shadow class
    _assert_method_from(el_web, 'click_into_center', WebElement)

    # Different driver types get different shadow classes when
    # `has_different_driver_types` is active (multi-driver scenario)
    assert type(el_mobile) is not type(el_web), 'Different drivers get different shadow classes'

    DriverWrapperSessions.all_sessions = []


def test_same_driver_elements_share_class():
    """Elements from the same driver share the same subclass."""
    DriverWrapperSessions.all_sessions = []

    appium_driver_cls = AppiumDriver
    appium_driver_cls.__init__ = lambda *a, **kw: None
    appium_driver_cls.session_id = None
    appium_driver_cls.command_executor = MagicMock()
    appium_driver_cls.error_handler = MagicMock()
    appium_driver_cls.capabilities = MagicMock(return_value={
        'platformName': 'ios', 'browserName': 'safari', 'automationName': 'safari'
    })()
    mobile_dw = MockedDW(Driver(driver=appium_driver_cls()))

    selenium_driver_cls = SeleniumDriver
    selenium_driver_cls.__init__ = lambda *a, **kw: None
    selenium_driver_cls.session_id = None
    selenium_driver_cls.command_executor = MagicMock()
    selenium_driver_cls.error_handler = MagicMock()
    selenium_driver_cls.caps = {}
    MockedDW(Driver(driver=selenium_driver_cls()))

    el1 = Element('a', driver_wrapper=mobile_dw)
    el2 = Element('b', driver_wrapper=mobile_dw)

    assert type(el1) is type(el2), (
        f'Elements with same driver should share class: '
        f'{type(el1).__name__} vs {type(el2).__name__}'
    )

    DriverWrapperSessions.all_sessions = []


class CustomElement(Element):
    custom_value = "custom_value"

    @property
    def value(self):
        return self.custom_value


def test_user_override_still_protected():
    """User-defined overrides should still be protected."""
    DriverWrapperSessions.all_sessions = []

    appium_driver_cls = AppiumDriver
    appium_driver_cls.__init__ = lambda *a, **kw: None
    appium_driver_cls.session_id = None
    appium_driver_cls.command_executor = MagicMock()
    appium_driver_cls.error_handler = MagicMock()
    appium_driver_cls.capabilities = MagicMock(return_value={
        'platformName': 'ios', 'browserName': 'safari', 'automationName': 'safari'
    })()

    dw = MockedDW(Driver(driver=appium_driver_cls()))
    el = CustomElement('test', driver_wrapper=dw)

    assert el.value == CustomElement.custom_value

    DriverWrapperSessions.all_sessions = []
