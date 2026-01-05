from __future__ import annotations

from abc import ABC
from typing import Union, List, Any

from PIL.Image import Image
from mops.keyboard_keys import KeyboardKeys
from playwright.sync_api import Error
from playwright.sync_api import Page as PlaywrightPage
from playwright.sync_api import Locator, Page, Browser, BrowserContext

from mops.mixins.objects.size import Size
from mops.mixins.objects.location import Location
from mops.utils.decorators import retry
from mops.utils.selector_synchronizer import get_platform_locator, set_playwright_locator
from mops.abstraction.element_abc import ElementABC
from mops.exceptions import InvalidSelectorException
from mops.utils.logs import Logging
from mops.shared_utils import cut_log_data, get_image
from mops.utils.internal_utils import (
    calculate_coordinate_to_click,
    is_group,
    is_element,
)


class PlayElement(ElementABC, Logging, ABC):

    instance: Browser
    context: BrowserContext
    driver: Page
    parent: Union[ElementABC, PlayElement]
    _element: Locator = None

    def __init__(self):  # noqa
        """
        Initializing of web element with playwright driver
        """
        self.locator = get_platform_locator(self)
        set_playwright_locator(self)

    # Element

    @property
    def element(self) -> Locator:
        """
        Get playwright Locator object

        :param: args: args from Locator object
        :param: kwargs: kwargs from Locator object
        :return: Locator
        """
        element = self._element
        if not element:
            driver = self._get_base()
            element = driver.locator(self.locator)

        return element

    @element.setter
    def element(self, base_element: Union[Locator, None]):
        """
        Element object setter. Try to avoid usage of this function

        :param: play_element: playwright Locator object
        """
        self._element = base_element
    
    @property
    def all_elements(self) -> Union[List[PlayElement], List[Any]]:
        """
        Returns a list of all matching elements.

        :return: A list of wrapped :class:`PlayElement` objects.
        """
        return self._get_all_elements(self.element.all())

    # Element interaction

    def click(self, *, force_wait: bool = True, **kwargs) -> PlayElement:
        """
        Clicks on the element.

        :param force_wait: If :obj:`True`, waits for element visibility before clicking.
        :type force_wait: bool

        **Selenium/Appium:**

        Selenium Safari using js click instead.

        :param kwargs: compatibility arg for playwright

        **Playwright:**

        :param kwargs: `any kwargs params from source API <https://playwright.dev/python/docs/api/class-locator#locator-click>`_

        :return: :class:`PlayElement`
        """
        self.log(f'Click into "{self.name}"')

        if force_wait:
            self.wait_visibility(silent=True)

        if self.driver_wrapper.is_mobile_resolution:
            self._first_element.tap(**kwargs)
        else:
            self._first_element.click(**kwargs)

        return self

    def click_outside(self, x: int = -5, y: int = -5) -> PlayElement:
        """
        Perform a click outside the current element, by default 5px left and above it.

        :param x: Horizontal offset from the element to click.
        :type x: int
        :param y: Vertical offset from the element to click.
        :type y: int
        :return: :class:`PlayElement`
        """
        self.log(f'Click outside from "{self.name}"')

        self._first_element.click(position={'x': float(x), 'y': float(y)}, force=True)
        return self


    def click_into_center(self, silent: bool = False) -> PlayElement:
        """
        Clicks at the center of the element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        if not self.is_fully_visible(silent=True):
            self.scroll_into_view()

        x, y = calculate_coordinate_to_click(self, 0, 0)

        if not silent:
            self.log(f'Click into the center (x: {x}, y: {y}) for "{self.name}"')

        self.driver_wrapper.click_by_coordinates(x=x, y=y, silent=True)
        return self


    def type_text(self, text: Union[str, KeyboardKeys], silent: bool = False) -> PlayElement:
        """
        Types text into the element.

        :param text: The text to be typed or a keyboard key.
        :type text: str, :class:`KeyboardKeys`
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        text = str(text)

        if not silent:
            self.log(f'Type text "{cut_log_data(text)}" into "{self.name}"')

        self._first_element.type(text=text)
        return self

    def type_slowly(self, text: str, sleep_gap: float = 0.05, silent: bool = False) -> PlayElement:
        """
        Types text into the element slowly with a delay between keystrokes.

        :param text: The text to be typed.
        :type text: str
        :param sleep_gap: Delay between keystrokes in seconds.
        :type sleep_gap: float
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        if not silent:
            self.log(f'Type text {cut_log_data(text)} into "{self.name}"')

        self._first_element.type(text=text, delay=sleep_gap)
        return self

    def clear_text(self, silent: bool = False) -> PlayElement:
        """
        Clears the text of the element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        if not silent:
            self.log(f'Clear text in "{self.name}"')

        self._first_element.fill('')
        return self

    def hover(self, silent: bool = False) -> PlayElement:
        """
        Hover the mouse over the current element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        if not silent:
            self.log(f'Hover over "{self.name}"')

        self._first_element.hover()
        return self

    def hover_outside(self, x: int = 0, y: int = -5) -> PlayElement:
        """
        Hover the mouse outside the current element, by default 5px above it.

        :param x: Horizontal offset from the element to hover.
        :type x: int
        :param y: Vertical offset from the element to hover.
        :type y: int
        :return: :class:`PlayElement`
        """
        self.log(f'Hover outside from "{self.name}"')
        self._first_element.hover(position={'x': float(x), 'y': float(y)}, force=True)
        return self

    def check(self) -> PlayElement:
        """
        Checks the checkbox element.

        :return: :class:`PlayElement`
        """
        self._first_element.check()

        return self

    def uncheck(self) -> PlayElement:
        """
        Unchecks the checkbox element.

        :return: :class:`PlayElement`
        """
        self._first_element.uncheck()

        return self

    # Element state

    def screenshot_image(self, screenshot_base: bytes = None) -> Image:
        """
        Returns a :class:`PIL.Image.Image` object representing the screenshot of the web element.
        Appium iOS: Take driver screenshot and crop manually element from it

        :param screenshot_base: Screenshot binary data (optional).
          If :obj:`None` is provided then takes a new screenshot
        :type screenshot_base: bytes
        :return: :class:`PIL.Image.Image`
        """
        screenshot_base = screenshot_base if screenshot_base else self.screenshot_base
        return get_image(screenshot_base)

    @property
    def screenshot_base(self) -> bytes:
        """
        Returns the binary screenshot data of the element.

        :return: :class:`bytes` - screenshot binary
        """
        return self._first_element.screenshot()

    @property
    def text(self) -> str:
        """
        Returns the text of the element.

        :return: :class:`str` - element text
        """
        return self.inner_text

    @property
    def inner_text(self) -> str:
        """
        Returns the inner text of the element.

        :return: :class:`str` - element inner text
        """
        return self._first_element.inner_text()

    @property
    def value(self) -> str:
        """
        Returns the value of the element.

        :return: :class:`str` - element value
        """
        return self._first_element.input_value()

    def is_available(self) -> bool:
        """
        Checks if the element is available in DOM tree.

        :return: :class:`bool` - :obj:`True` if present in DOM
        """
        return bool(len(self.element.element_handles()))

    def is_displayed(self, silent: bool = False) -> bool:
        """
        Checks if the element is displayed.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        if not silent:
            self.log(f'Check visibility of "{self.name}"')

        try:
            return self._first_element.is_visible()
        except Error as exc:
            raise InvalidSelectorException(exc.message)


    def is_hidden(self, silent: bool = False) -> bool:
        """
        Checks if the element is hidden.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        if not silent:
            self.log(f'Check invisibility of "{self.name}"')

        return self._first_element.is_hidden()

    def get_attribute(self, attribute: str, silent: bool = False) -> str:
        """
        Retrieve a specific attribute from the current element.

        :param attribute: The name of the attribute to retrieve, such as 'value', 'innerText', 'textContent', etc.
        :type attribute: str
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`str` - The value of the specified attribute.
        """
        if not silent:
            self.log(f'Get "{attribute}" from "{self.name}"')

        return self._first_element.get_attribute(attribute)

    def get_all_texts(self, silent: bool = False) -> List:
        """
        Retrieve text content from all matching elements.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`list` of :class:`str` - A list containing the text content of all matching elements.
        """
        if not silent:
            self.log(f'Get all texts from "{self.name}"')

        return self.element.all_text_contents()

    def get_elements_count(self, silent: bool = False) -> int:
        """
        Get the count of matching elements.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`int` - The number of matching elements.
        """
        if not silent:
            self.log(f'Get elements count of "{self.name}"')

        return len(self.all_elements)

    @retry(AttributeError)
    def get_rect(self) -> dict:
        """
        Retrieve the size and position of the element as a dictionary.

        :return: :class:`dict` - A dictionary {'x', 'y', 'width', 'height'} of the element.
        """
        sorted_items: list = sorted(self.element.bounding_box().items(), reverse=True)
        return dict(sorted_items)

    @property
    @retry(TypeError)
    def size(self) -> Size:
        """
        Get the size of the current element, including width and height.

        :return: :class:`.Size` - An object representing the element's dimensions.
        """
        box = self.element.first.bounding_box()
        return Size(width=box['width'], height=box['height'])

    @property
    @retry(TypeError)
    def location(self) -> Location:
        """
        Get the location of the current element, including the x and y coordinates.

        :return: :class:`Location` - An object representing the element's position.
        """
        box = self.element.first.bounding_box()
        return Location(x=box['x'], y=box['y'])

    def is_enabled(self, silent: bool = False) -> bool:
        """
        Check if the current element is enabled.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool` - :obj:`True` if the element is enabled, :obj:`False` otherwise.
        """
        if not silent:
            self.log(f'Check is element "{self.name}" enabled')

        return self._first_element.is_enabled()

    def is_checked(self) -> bool:
        """
        Check if a checkbox or radio button is selected.

        :return: :class:`bool` - :obj:`True` if the checkbox or radio button is checked, :obj:`False` otherwise.
        """
        return self._first_element.is_checked()

    # Mixin

    def _get_base(self) -> Union[PlaywrightPage, Locator]:
        """
        Get driver depends on parent element if available

        :return: driver
        """
        base = self.driver
        if self.parent:
            self.log(f'Get element "{self.name}" from parent element "{self.parent.name}"', level='debug')

            if is_group(self.parent) or is_element(self.parent):
                base = self.parent.element

        return base

    @property
    def _first_element(self):
        """
        Get first element

        :return: first element
        """
        return self.element.first
