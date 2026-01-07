from __future__ import annotations

from dataclasses import astuple
from typing import List

from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver

from mops.mixins.objects.size import Size
from mops.selenium.core.core_driver import CoreDriver
from mops.mixins.objects.driver import Driver


class WebDriver(CoreDriver):

    def __init__(self, driver_container: Driver, *args, **kwargs):  # noqa
        """
        Initializing of desktop web driver with selenium

        :param driver_container: Driver that contains selenium driver object
        """
        self.driver : SeleniumWebDriver = driver_container.driver
        self.is_desktop = True
        self.original_tab = self.driver.current_window_handle
        self.browser_name = self.driver.caps.get('browserName', None)

        CoreDriver.__init__(self, driver=self.driver)

    def set_window_size(self, size: Size) -> WebDriver:
        """
        Set the inner window size (viewport) of the current browser context.

        :param size: The desired inner window size as a :class:`.Size` object.
        :return: The current instance of :obj:`.WebDriver`.
        """
        width, height = astuple(size)

        if self.is_desktop:
            outer_width, outer_height = astuple(self.get_window_size())
            inner_width, inner_height = astuple(self.get_inner_window_size())

            width += outer_width - inner_width
            height += outer_height - inner_height

        self.driver.set_window_size(width, height)
        return self

    def get_all_tabs(self) -> List[str]:
        """
        Selenium/Playwright only: Retrieve all opened tabs.

        :return: A list of :class:`str`, each representing an open tab.
        :rtype: typing.List[str]
        """
        return self.driver.window_handles

    def create_new_tab(self) -> WebDriver:
        """
        Selenium/Playwright only: Create a new tab and switch to it.

        :return: :obj:`.WebDriver` - The current instance of the driver wrapper, now switched to the new tab.
        """
        self.driver.switch_to.new_window('tab')
        return self

    def switch_to_original_tab(self) -> WebDriver:
        """
        Selenium/Playwright only: Switch back to the original tab.

        :return: :obj:`.WebDriver` - The current instance of the driver wrapper, now switched to the original tab.
        """
        self.driver.switch_to.window(self.original_tab)
        return self

    def switch_to_tab(self, tab: int = -1) -> WebDriver:
        """
        Selenium/Playwright only: Switch to a specific tab.

        :param tab: The index of the tab to switch to, starting from 1. Default is the latest tab.
        :type tab: int
        :return: :obj:`.WebDriver` - The current instance of the driver wrapper, now switched to the specified tab.
        """
        if tab == -1:
            tab = self.get_all_tabs()[tab]
        else:
            tab = self.get_all_tabs()[tab - 1]

        self.driver.switch_to.window(tab)
        return self

    def close_unused_tabs(self) -> WebDriver:
        """
        Selenium/Playwright only: Close all tabs except the original.

        :return: :obj:`.WebDriver` - The current instance of the driver wrapper,
          with all tabs except the original closed.
        """
        tabs = self.get_all_tabs()
        tabs.remove(self.original_tab)

        for tab in tabs:
            self.driver.switch_to.window(tab)
            self.driver.close()

        return self.switch_to_original_tab()
