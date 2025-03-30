from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from mops.base.driver_wrapper import DriverWrapper, DriverWrapperSessions

if TYPE_CHECKING:
    from appium.webdriver.webdriver import WebDriver as AppiumWebDriver
    from playwright.sync_api import Page as PlaywrightSourcePage
    from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver


def get_driver_wrapper_from_object(obj: Union[DriverWrapper, Any]):
    """
    Retrieves the driver wrapper from a given object. The object can either be a :class:`.DriverWrapper` instance
      or an object that contains a ``driver_wrapper`` attribute.

    :param obj: The source object, which can either be a :class:`.DriverWrapper` instance or an object that
      contains a `driver_wrapper` attribute.
    :type obj: :class:`.DriverWrapper` or :obj:`typing.Any`
    :return: The extracted :class:`.DriverWrapper` instance.
    :raises Exception: If the object does not contain a ``driver_wrapper`` attribute or is of an invalid type.
    """
    if obj is None:
        return DriverWrapperSessions.first_session()

    if isinstance(obj, DriverWrapper):
        driver_wrapper_instance = obj
    elif hasattr(obj, 'driver_wrapper'):
        driver_wrapper_instance = obj.driver_wrapper
    else:
        obj_nfo = f'"{obj.name}" of "{obj.__class__}"' if obj else obj
        msg = f'Cant get driver_wrapper from {obj_nfo}'
        raise Exception(msg)

    return driver_wrapper_instance


class DriverMixin:

    _driver_wrapper = None

    @property
    def driver(self) -> Union[SeleniumWebDriver, AppiumWebDriver, PlaywrightSourcePage]:
        r"""
        Retrieves the source driver instance, which could be a Selenium, Appium, or Playwright driver.

        :return: Current source driver that assigned for this object, which is either \n
          :class:`selenium.webdriver.remote.webdriver.WebDriver` or\n
          :class:`appium.webdriver.webdriver.WebDriver` or\n
          :class:`playwright.sync_api.Page` instance.
        """
        return getattr(self.driver_wrapper, 'driver', None)

    @property
    def driver_wrapper(self) -> DriverWrapper:
        """
        Retrieves the driver wrapper instance.

        :return: The current :obj:`.DriverWrapper` instance that assigned for this object.
        :rtype: DriverWrapper
        """
        return self._driver_wrapper

    @driver_wrapper.setter
    def driver_wrapper(self, driver_wrapper: DriverWrapper) -> None:
        """
        Sets the driver wrapper instance, for this object.

        :param driver_wrapper: The :class:`.DriverWrapper` instance to be set.
        :type driver_wrapper: DriverWrapper
        """
        self._driver_wrapper = driver_wrapper
