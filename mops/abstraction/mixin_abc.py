from abc import ABC
from typing import Any, NoReturn, Union

from appium.webdriver.webdriver import WebDriver as AppiumWebDriver
from playwright.sync_api import Page as PlaywrightSourcePage
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver

from mops.base.driver_wrapper import DriverWrapper
from mops.utils.logs import LogLevel


class MixinABC(ABC):

    @property
    def driver(self) -> Union[SeleniumWebDriver, AppiumWebDriver, PlaywrightSourcePage]:
        r"""
        Retrieves the source driver instance, which could be a Selenium, Appium, or Playwright driver.

        :return: Current source driver that assigned for this object, which is either \n
          :class:`selenium.webdriver.remote.webdriver.WebDriver` or\n
          :class:`appium.webdriver.webdriver.WebDriver` or\n
          :class:`playwright.sync_api.Page` instance.
        """
        raise NotImplementedError

    @property
    def driver_wrapper(self) -> DriverWrapper:
        """
        Retrieves the driver wrapper instance.

        :return: The current :obj:`.DriverWrapper` instance that assigned for this object.
        :rtype: DriverWrapper
        """
        raise NotImplementedError

    @driver_wrapper.setter
    def driver_wrapper(self, driver_wrapper: DriverWrapper) -> NoReturn:
        """
        Sets the driver wrapper instance, for this object.

        :param driver_wrapper: The DriverWrapper instance to be set.
        :type driver_wrapper: DriverWrapper
        """
        raise NotImplementedError

    def log(self: Any, message: str, level: str = LogLevel.INFO) -> None:
        """
        Logs a message with detailed context in the following format:

        .. code-block:: text

           # Format
           [time][level][driver_index][module][function:line] <message>
           # Example
           [Aug 14][16:04:22.767][I][2_driver][play_element.py][is_displayed:328] Check visibility of "Mouse page"

        :param message: The log message to record.
        :type message: str
        :param level: The logging level, which should be one of the values from :class:`LogLevel`
        :type level: str
        :return: :obj:`None`
        """
        raise NotImplementedError
