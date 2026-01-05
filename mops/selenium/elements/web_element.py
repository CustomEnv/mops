from __future__ import annotations

from abc import ABC

from selenium.common import JavascriptException

from mops.selenium.core.core_element import CoreElement
from mops.js_scripts import js_click
from mops.utils.decorators import retry
from mops.utils.internal_utils import calculate_coordinate_to_click
from mops.utils.selector_synchronizer import get_platform_locator, set_selenium_selector


class WebElement(CoreElement, ABC):

    def __init__(self):
        """
        Initializing of web element with selenium driver
        """
        self.locator = get_platform_locator(self)
        set_selenium_selector(self)

    def click(self, *, force_wait: bool = True, **kwargs) -> WebElement:
        """
        Clicks on the element.

        :param force_wait: If :obj:`True`, waits for element visibility before clicking.
        :type force_wait: bool

        **Selenium/Appium:**

        Selenium Safari using js click instead.

        :param kwargs: compatibility arg for playwright

        **Playwright:**

        :param kwargs: `any kwargs params from source API <https://playwright.dev/python/docs/api/class-locator#locator-click>`_

        :return: :class:`WebElement`
        """
        if self.driver_wrapper.is_safari:
            self.log(f'Click into "{self.name}"')
            self.execute_script(js_click)
        else:
            CoreElement.click(self, force_wait=force_wait, **kwargs)

        return self

    @retry(JavascriptException)
    def hover(self, silent: bool = False) -> WebElement:
        """
        Hover the mouse over the current element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`WebElement`
        """
        if not silent:
            self.log(f'Hover over "{self.name}"')

        self._action_chains\
            .move_to_element(self.element)\
            .move_by_offset(1, 1)\
            .move_to_element(self.element)\
            .perform()
        return self

    @retry(JavascriptException)
    def hover_outside(self, x: int = 0, y: int = -5) -> WebElement:
        """
        Hover the mouse outside the current element, by default 5px above it.

        :param x: Horizontal offset from the element to hover.
        :type x: int
        :param y: Vertical offset from the element to hover.
        :type y: int
        :return: :class:`WebElement`
        """
        self.log(f'Hover outside from "{self.name}"')

        if not self.is_fully_visible(silent=True):
            self.scroll_into_view()

        x, y = calculate_coordinate_to_click(self, x, y)
        self._action_chains\
            .move_to_location(x, y)\
            .perform()
        return self

    @retry(JavascriptException)
    def click_outside(self, x: int = -5, y: int = -5) -> WebElement:
        """
        Perform a click outside the current element, by default 5px left and above it.

        :param x: Horizontal offset from the element to click.
        :type x: int
        :param y: Vertical offset from the element to click.
        :type y: int
        :return: :class:`WebElement`
        """
        self.log(f'Click outside from "{self.name}"')

        if not self.is_fully_visible(silent=True):
            self.scroll_into_view()

        x, y = calculate_coordinate_to_click(self, x, y)

        self.driver_wrapper.click_by_coordinates(x=x, y=y, silent=True)
        return self

    @retry(JavascriptException)
    def click_into_center(self, silent: bool = False) -> WebElement:
        """
        Clicks at the center of the element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`WebElement`
        """
        if not self.is_fully_visible(silent=True):
            self.scroll_into_view()

        x, y = calculate_coordinate_to_click(self, 0, 0)

        if not silent:
            self.log(f'Click into the center (x: {x}, y: {y}) for "{self.name}"')

        self.driver_wrapper.click_by_coordinates(x=x, y=y, silent=True)
        return self
