from __future__ import annotations

import os
from typing import Union

from PIL import Image
from appium.webdriver.webdriver import WebDriver as AppiumWebDriver
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver
from playwright.sync_api import Locator as PlaywrightWebElement, Browser
from selenium.webdriver.remote.webelement import WebElement as SeleniumWebElement
from appium.webdriver.webelement import WebElement as AppiumWebElement

from dyatel.visual_comparison import assert_same_images


def get_child_elements(self, instance):
    """Return page elements and page objects of this page object

    :returns: list of page elements and page objects
    """
    elements = []

    class_items = list(self.__dict__.items()) + list(self.__class__.__dict__.items())

    for parent_class in self.__class__.__bases__:
        class_items += list(parent_class.__dict__.items()) + list(parent_class.__class__.__dict__.items())

    for attribute, value in class_items:
        if isinstance(value, instance):
            elements.append(value)
    return set(elements)


def get_timeout(timeout):
    if timeout < 100:  # for timeout in ms
        timeout *= 1000
    return timeout


def calculate_coordinate_to_click(element, x, y):
    """
    Calculate coordinates to click for element
    Examples:
        (0, 0) -- center of the element
        (5, 0) -- 5 pixels to the right
        (-10, 0) -- 10 pixels to the left out of the element
        (0, -5) -- 5 pixels below the element

    :param element: dyatel WebElement or MobileElement
    :param x: horizontal offset relative to either left (x < 0) or right side (x > 0)
    :param y: vertical offset relative to either top (y > 0) or bottom side (y < 0)
    :return:  coordinates
    """
    element_size = element.element.size
    half_width, half_height = element_size['width'] / 2, element_size['height'] / 2
    dx, dy = half_width, half_height
    if x:
        dx += x + (-half_width if x < 0 else half_width)
    if y:
        dy += -y + (half_height if y < 0 else -half_height)
    return dx, dy


class Mixin:
    """ Mixin for PlayElement and CoreElement """
    driver: Union[AppiumWebDriver, SeleniumWebDriver, Browser] = None  # variable placeholder
    parent = None  # variable placeholder
    locator: str = ''  # variable placeholder
    locator_type: str = ''  # variable placeholder
    get_screenshot = None  # variable placeholder
    element: Union[SeleniumWebElement, AppiumWebElement, PlaywrightWebElement] = None   # variable placeholder

    def get_element_logging_data(self, element=None) -> str:
        """
        Get full loging data depends on parent element

        :param element: element to collect log data
        :return: log string
        """
        element = element if element else self
        parent = element.parent
        current_data = f'Selector: ["{element.locator_type}": "{element.locator}"]'
        if parent:
            parent_data = f'Parent selector: ["{parent.locator_type}": "{parent.locator}"]'
            current_data = f'{current_data}. {parent_data}'
        return current_data

    def assert_screenshot(self, filename, threshold=0) -> Mixin:
        """
        Assert given (by name) and taken screenshot equals

        :param filename: screenshot path/name
        :param threshold: possible threshold
        :return: current driver instance (Web/Mobile/PlayDriver)
        """
        root_path = os.environ.get('visual', '')
        reference_file = f'{root_path}/reference/{filename}.png'

        try:
            Image.open(reference_file)
        except FileNotFoundError:
            self.get_screenshot(reference_file)
            message = 'Reference file not found, but its just saved. ' \
                      'If it CI run, then you need to commit reference files.'
            raise FileNotFoundError(message) from None

        output_file = f'{root_path}/output/{filename}.png'
        self.get_screenshot(output_file)
        assert_same_images(output_file, reference_file, filename, threshold)
        return self
