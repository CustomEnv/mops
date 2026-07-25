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


class CustomElement(Element):
    custom_value = "custom_value"

    @property
    def value(self):
        return self.custom_value



def test_elements_get_own_driver_methods(mocked_ios_driver, mocked_selenium_driver):
    """Elements from the last driver type set the class-level methods."""
    el_mobile = Element('m1', driver_wrapper=mocked_ios_driver)
    _assert_method_from(el_mobile, 'click_into_center', MobileElement)

    el_web = Element('w1', driver_wrapper=mocked_selenium_driver)
    _assert_method_from(el_web, 'click_into_center', WebElement)

    assert type(el_mobile) is not type(el_web), 'Different drivers get different shadow classes'


def test_same_driver_elements_share_class(mocked_ios_driver, mocked_selenium_driver):
    """Elements from the same driver share the same subclass."""
    el1 = Element('a', driver_wrapper=mocked_ios_driver)
    el2 = Element('b', driver_wrapper=mocked_ios_driver)

    assert type(el1) is type(el2), (
        f'Elements with same driver should share class: '
        f'{type(el1).__name__} vs {type(el2).__name__}'
    )


def test_user_override_still_protected(mocked_ios_driver):
    """User-defined overrides should still be protected."""
    el = CustomElement('test', driver_wrapper=mocked_ios_driver)

    assert el.value == CustomElement.custom_value


def test_base_element_pollution_does_not_leak_to_subclass(mocked_ios_driver, mocked_selenium_driver):
    """
    Reproduces the bug: base Element initialised with Appium pollutes
    Element.__dict__ with MobileElement methods. A subclass initialised
    with Selenium must get WebElement methods, not MobileElement ones.
    """
    mobile_el = Element('base', driver_wrapper=mocked_ios_driver)
    _assert_method_from(mobile_el, 'click_into_center', MobileElement)

    web_el = CustomElement('sub', driver_wrapper=mocked_selenium_driver)
    _assert_method_from(web_el, 'click_into_center', WebElement)
    assert web_el.value == CustomElement.custom_value
    assert type(web_el).__name__ == 'CustomElement', 'Shadow class must keep original name'
