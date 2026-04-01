from __future__ import annotations

import time
from abc import ABC

from PIL.Image import Image

from mops.selenium.core.core_element import CoreElement
from mops.mixins.objects.location import Location
from mops.mixins.objects.size import Size
from mops.utils.internal_utils import calculate_coordinate_to_click
from mops.utils.selector_synchronizer import get_platform_locator, set_appium_selector


class MobileElement(CoreElement, ABC):

    def click_outside(self, x: int = -5, y: int = -5) -> MobileElement:
        """
        Perform a click outside the current element, by default 5px left and above it.

        :param x: Horizontal offset from the element to click.
        :type x: int
        :param y: Vertical offset from the element to click.
        :type y: int
        :return: :class:`MobileElement`
        """
        if self.driver_wrapper.is_web_context:
            if not self.is_fully_visible(silent=True):
                self.scroll_into_view()

        x, y = calculate_coordinate_to_click(self, x, y)

        if self.driver_wrapper.is_ios:
            y += self.driver_wrapper.top_bar_height

        self.log(f'Tap outside from "{self.name}" with coordinates (x: {x}, y: {y})')

        self.driver_wrapper.click_by_coordinates(x=x, y=y, silent=True)
        return self

    def click_into_center(self, silent: bool = False) -> MobileElement:
        """
        Clicks at the center of the element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`MobileElement`
        """
        if self.driver_wrapper.is_web_context:
            if not self.is_fully_visible(silent=True):
                self.scroll_into_view()

        x, y = calculate_coordinate_to_click(self, 0, 0)

        if self.driver_wrapper.is_ios:
            y += self.driver_wrapper.top_bar_height

        if not silent:
            self.log(f'Tap into the center by coordinates (x: {x}, y: {y}) for "{self.name}"')

        self.driver_wrapper.click_by_coordinates(x, y, silent=True)

        return self

    def hover(self, silent: bool = False) -> MobileElement:
        """
        Hover the mouse over the current element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`MobileElement`
        """
        if not silent:
            self.log(f'Hover over "{self.name}"')

        self.click_into_center()
        return self

    def hover_outside(self, x: int = 0, y: int = -5) -> MobileElement:
        """
        Hover the mouse outside the current element, by default 5px above it.

        :param x: Horizontal offset from the element to hover.
        :type x: int
        :param y: Vertical offset from the element to hover.
        :type y: int
        :return: :class:`MobileElement`
        """
        return self.click_outside(x=x, y=y)

    def click_in_alert(self) -> MobileElement:
        """
        Perform a click on an element inside an alert box (Mobile only).
        **Note:** Automatically switches to native context of the browser.

        :return: :class:`MobileElement`
        """
        try:
            self.driver_wrapper.switch_to_native()
            time.sleep(1)
            if self.wait_visibility_without_error(timeout=5, silent=True).is_displayed(silent=True):
                self.click()
        finally:
            self.driver_wrapper.switch_to_web()

        return self

    def screenshot_image(self, screenshot_base: bytes = None) -> Image:
        """
        Returns a :class:`PIL.Image.Image` object representing the screenshot of the web element.
        Appium iOS: Take driver screenshot and crop manually element from it

        :param screenshot_base: Screenshot binary data (optional).
          If :obj:`None` is provided then takes a new screenshot
        :type screenshot_base: bytes
        :return: :class:`PIL.Image.Image`
        """
        if self.driver_wrapper.is_ios:
            element_box = self._element_box()
            window_height = self.driver.get_window_size()['height']
            image = self.driver_wrapper.screenshot_image()

            if window_height > self.size.height:
                image = image.crop(element_box)

        else:
            image = CoreElement.screenshot_image(self, screenshot_base)

        return image

    @property
    def size(self) -> Size:
        """
        Get the size of the current element, including width and height.

        :return: :class:`.Size` - An object representing the element's dimensions.
        """
        if self.driver_wrapper.is_native_context:
            return Size(**self.element.size)

        return CoreElement.size.fget(self)

    @property
    def location(self) -> Location:
        """
        Get the location of the current element, including the x and y coordinates.

        :return: :class:`Location` - An object representing the element's position.
        """
        if self.driver_wrapper.is_native_context:
            return Location(**self.element.location)

        return CoreElement.location.fget(self)

    def _element_box(self) -> tuple:
        """
        Get element coordinates on screen for ios safari

        :return: element coordinates on screen (start_x, start_y, end_x, end_y)
        """
        element_size = self.size
        element_location = self.location

        return (
            element_location.x,
            element_location.y,
            element_location.x + element_size.width,
            element_location.y + element_size.height,
        )

    def _set_locator(self):
        self.locator = get_platform_locator(self)
        set_appium_selector(self)
        self._is_locator_configured = True
