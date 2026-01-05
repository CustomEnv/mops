from __future__ import annotations

import time
from abc import ABC
from typing import Union, List, Any, Callable, TYPE_CHECKING

from PIL import Image

from mops.mixins.internal_mixin import get_element_info
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver
from selenium.webdriver.remote.webelement import WebElement as SeleniumWebElement
from appium.webdriver.webelement import WebElement as AppiumWebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    InvalidArgumentException as SeleniumInvalidArgumentException,
    InvalidSelectorException as SeleniumInvalidSelectorException,
    NoSuchElementException as SeleniumNoSuchElementException,
    StaleElementReferenceException as SeleniumStaleElementReferenceException,
    WebDriverException as SeleniumWebDriverException,
)
from mops.abstraction.element_abc import ElementABC
from mops.selenium.sel_utils import ActionChains
from mops.js_scripts import get_element_size_js, get_element_position_on_screen_js, hide_caret_js_script
from mops.keyboard_keys import KeyboardKeys
from mops.mixins.objects.location import Location
from mops.mixins.objects.size import Size
from mops.shared_utils import cut_log_data, _scaled_screenshot
from mops.utils.internal_utils import WAIT_EL, safe_call, get_dict, is_group
from mops.utils.decorators import retry
from mops.exceptions import (
    InvalidSelectorException,
    DriverWrapperException,
    NoSuchElementException,
    ElementNotInteractableException,
    NoSuchParentException,
)

if TYPE_CHECKING:
    from mops.base.element import Element


class CoreElement(ElementABC, ABC):

    parent: Union[Element]
    locator_type: str
    _element: Union[None, SeleniumWebElement, AppiumWebElement] = None
    _cached_element: Union[None, SeleniumWebElement, AppiumWebElement] = None

    # Element

    @property
    def element(self) -> SeleniumWebElement:
        """
        Get selenium WebElement object

        :return: SeleniumWebElement
        """
        return self._get_element()

    @element.setter
    def element(self, base_element: Union[SeleniumWebElement, AppiumWebElement]):
        """
        Core element setter. Try to avoid usage of this function

        :param base_element: selenium WebElement or appium WebElement
        """
        self._element = base_element

    @property
    def all_elements(self) -> Union[List[CoreElement], List[Any]]:
        """
        Returns a list of all matching elements.

        :return: A list of wrapped :class:`CoreElement` objects.
        """
        return self._get_all_elements(self._find_elements())

    # Element interaction

    @retry(ElementNotInteractableException)
    def click(self, *, force_wait: bool = True, **kwargs) -> CoreElement:
        """
        Clicks on the element.

        :param force_wait: If :obj:`True`, waits for element visibility before clicking.
        :type force_wait: bool

        **Selenium/Appium:**

        Selenium Safari using js click instead.

        :param kwargs: compatibility arg for playwright

        **Playwright:**

        :param kwargs: `any kwargs params from source API <https://playwright.dev/python/docs/api/class-locator#locator-click>`_

        :return: :class:`CoreElement`
        """
        self.log(f'Click into "{self.name}"')

        if force_wait:
            self.wait_visibility(silent=True)

        try:
            self.wait_enabled(silent=True).element.click()
            return self
        except SeleniumWebDriverException as exc:
            selenium_exc_msg = exc.msg

        raise ElementNotInteractableException(
            f'Element "{self.name}" not interactable. {self.get_element_info()}. '
            f'Original error: {selenium_exc_msg}'
        )

    def type_text(self, text: Union[str, KeyboardKeys], silent: bool = False) -> CoreElement:
        """
        Types text into the element.

        :param text: The text to be typed or a keyboard key.
        :type text: str, :class:`KeyboardKeys`
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`CoreElement`
        """
        text = str(text)

        if not silent:
            self.log(f'Type text "{cut_log_data(text)}" into "{self.name}"')

        self.element.send_keys(text)

        return self

    def type_slowly(self, text: str, sleep_gap: float = 0.05, silent: bool = False) -> CoreElement:
        """
        Types text into the element slowly with a delay between keystrokes.

        :param text: The text to be typed.
        :type text: str
        :param sleep_gap: Delay between keystrokes in seconds.
        :type sleep_gap: float
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`CoreElement`
        """
        text = str(text)

        if not silent:
            self.log(f'Type text "{cut_log_data(text)}" into "{self.name}"')

        element = self.element
        for letter in str(text):
            element.send_keys(letter)
            time.sleep(sleep_gap)

        return self

    def clear_text(self, silent: bool = False) -> CoreElement:
        """
        Clears the text of the element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`CoreElement`
        """
        if not silent:
            self.log(f'Clear text in "{self.name}"')

        self.element.clear()

        return self

    def check(self) -> CoreElement:
        """
        Checks the checkbox element.

        :return: :class:`CoreElement`
        """
        self.element = self._get_element(wait_strategy=self.wait_availability)

        try:
            if not self.is_checked():
                self.click(force_wait=False)
        finally:
            self.element = None

        return self

    def uncheck(self) -> CoreElement:
        """
        Unchecks the checkbox element.

        :return: :class:`CoreElement`
        """
        self.element = self._get_element(wait_strategy=self.wait_availability)

        try:
            if self.is_checked():
                self.click(force_wait=False)
        finally:
            self.element = None

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
        element_size = self.size.width
        screenshot_base = screenshot_base if screenshot_base else self.screenshot_base
        return _scaled_screenshot(screenshot_base, element_size)

    @property
    def screenshot_base(self) -> bytes:
        """
        Returns the binary screenshot data of the element.

        :return: :class:`bytes` - screenshot binary
        """
        self.execute_script(hide_caret_js_script)

        return self.element.screenshot_as_png

    @property
    @retry(SeleniumStaleElementReferenceException)
    def text(self) -> str:
        """
        Returns the text of the element.

        :return: :class:`str` - element text
        """
        element = self._get_element(wait_strategy=self.wait_availability)

        if self.driver_wrapper.is_safari:
            return element.get_attribute('innerText')

        return element.text

    @property
    def inner_text(self) -> str:
        """
        Returns the inner text of the element.

        :return: :class:`str` - element inner text
        """
        return self.get_attribute('textContent', silent=True) or self.get_attribute('innerText', silent=True)

    @property
    def value(self) -> str:
        """
        Returns the value of the element.

        :return: :class:`str` - element value
        """
        value = self.get_attribute('value', silent=True)
        return '' if value is None else value

    def is_available(self) -> bool:
        """
        Checks if the element is available in DOM tree.

        :return: :class:`bool` - :obj:`True` if present in DOM
        """
        if self._element:
            return self._is_element_still_available(self._element)

        try:
            element = bool(safe_call(self._find_element, wait_parent=False))
        except SeleniumInvalidSelectorException as exc:
            raise InvalidSelectorException(exc.msg)

        return element

    def is_displayed(self, silent: bool = False) -> bool:
        """
        Checks if the element is displayed.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        is_displayed = self.is_available()

        if is_displayed:
            desired_element = self._element or self._cached_element
            is_displayed = bool(safe_call(desired_element.is_displayed))

        if not silent:
            self.log(f'Check displaying of "{self.name}" - {is_displayed}')

        return is_displayed

    def is_hidden(self, silent: bool = False) -> bool:
        """
        Checks if the element is hidden.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        status = not self.is_displayed(silent=True)

        if not silent:
            self.log(f'Check invisibility of "{self.name}" - {status}')

        return status

    @retry(SeleniumStaleElementReferenceException)
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

        return self.element.get_attribute(attribute)

    def get_all_texts(self, silent: bool = False) -> List[str]:
        """
        Retrieve text content from all matching elements.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`list` of :class:`str` - A list containing the text content of all matching elements.
        """
        if not silent:
            self.log(f'Get all texts from "{self.name}"')

        self.wait_visibility(silent=True)

        return list(element_item.text for element_item in self.all_elements)

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

    def get_rect(self) -> dict:
        """
        Retrieve the size and position of the element as a dictionary.

        :return: :class:`dict` - A dictionary {'x', 'y', 'width', 'height'} of the element.
        """
        sorted_items = sorted({**get_dict(self.size), **get_dict(self.location)}.items(), reverse=True)
        return dict(sorted_items)

    @property
    @retry(SeleniumStaleElementReferenceException)
    def size(self) -> Size:
        """
        Get the size of the current element, including width and height.

        :return: :class:`.Size` - An object representing the element's dimensions.
        """
        return Size(**self.execute_script(get_element_size_js))

    @property
    @retry(SeleniumStaleElementReferenceException)
    def location(self) -> Location:
        """
        Get the location of the current element, including the x and y coordinates.

        :return: :class:`Location` - An object representing the element's position.
        """
        return Location(**self.execute_script(get_element_position_on_screen_js))

    def is_enabled(self, silent: bool = False) -> bool:
        """
        Check if the current element is enabled.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool` - :obj:`True` if the element is enabled, :obj:`False` otherwise.
        """
        if not silent:
            self.log(f'Check is element "{self.name}" enabled')

        return self.element.is_enabled()

    def is_checked(self) -> bool:
        """
        Check if a checkbox or radio button is selected.

        :return: :class:`bool` - :obj:`True` if the checkbox or radio button is checked, :obj:`False` otherwise.
        """
        return self._get_element(wait_strategy=self.wait_availability).is_selected()

    # Mixin

    def _get_wait(self, timeout: int = WAIT_EL) -> WebDriverWait:
        """
        Get wait with depends on parent element if available

        :return: driver
        """
        return WebDriverWait(self.driver, timeout)

    @property
    def _action_chains(self) -> ActionChains:
        """
        Get action chains with depends on parent element if available

        :return: ActionChains
        """
        return ActionChains(self.driver)

    def _get_element(self, wait_strategy: Union[bool, Callable] = True, force_wait: bool = False) -> SeleniumWebElement:
        """
        Get selenium element from driver or parent element

        :param wait_strategy: wait strategy for element and/or element parent before grab
        :param force_wait: force wait for some element
        :return: SeleniumWebElement
        """
        element = None
        if self._is_element_still_available(self._element):
            element = self._element

        if wait_strategy is True:
            wait_strategy = self.wait_visibility

        if not element:

            # Try to get element instantly without wait. Skipped if force_wait given
            if not force_wait:
                element = safe_call(self._find_element, wait_parent=False)

            # Wait for element if it is not found instantly
            if (not element and wait_strategy) or force_wait:
                element = self._get_cached_element(safe_call(wait_strategy, silent=True))

        if not element:
            element_info = f'"{self.name}" {self.__class__.__name__}'
            if self.parent and not self._get_cached_element(self.parent):
                raise NoSuchParentException(
                    f'{self._get_container_info()} container not found while accessing {element_info}. '
                    f'{get_element_info(self.parent, "Container Selector=")}'
                )

            raise NoSuchElementException(
                f'Unable to locate the {element_info}. '
                f'{self.get_element_info()}'
                f'{self._ensure_unique_parent()}'
            )

        return element

    def _get_base(self, wait_strategy: Union[bool, Callable] = True) -> Union[SeleniumWebDriver, SeleniumWebElement]:
        """
        Get driver with depends on parent element if available

        :return: driver
        """
        base = self.driver

        if not base:
            raise DriverWrapperException("Can't find driver")

        if self.driver_wrapper.is_appium:
            if self.driver_wrapper.is_native_context:
                return base

        if self.parent:
            base = self.parent._get_element(wait_strategy=wait_strategy)

        return base

    def _find_element(self, wait_parent: bool = False) -> Union[SeleniumWebElement, AppiumWebElement]:
        """
        Find selenium/appium element

        :param wait_parent: wait for base(parent) element
        :return: SeleniumWebElement or AppiumWebElement
        """
        base = self._get_base(wait_strategy=wait_parent)
        self._cached_element = None

        try:
            element = base.find_element(self.locator_type, self.locator)
            self._cached_element = element
            return element
        except (SeleniumInvalidArgumentException, SeleniumInvalidSelectorException) as exc:
            self._raise_invalid_selector_exception(exc)
        except SeleniumNoSuchElementException as exc:
            raise NoSuchElementException(exc.msg)

    def _find_elements(self, wait_parent: bool = False) -> List[Union[SeleniumWebElement, AppiumWebElement]]:
        """
        Find all selenium/appium elements

        :param wait_parent: wait for base(parent) element
        :return: list of SeleniumWebElement or AppiumWebElement
        """
        base = self._get_base(wait_strategy=wait_parent)
        self._cached_element = None

        try:
            elements = base.find_elements(self.locator_type, self.locator)

            if elements:
                self._cached_element = elements[0]

            return elements
        except (SeleniumInvalidArgumentException, InvalidSelectorException) as exc:
            self._raise_invalid_selector_exception(exc)

    def _raise_invalid_selector_exception(self, exc: Any) -> None:
        """
        Raises InvalidSelectorException if specific keywords in exception message

        :param exc: original exc object
        :return: None
        """
        if 'invalid locator' in exc.msg or 'is not a valid' in exc.msg:
            msg = f'Selector for "{self.name}" is invalid. {self.get_element_info()}'
            raise InvalidSelectorException(msg)
        else:
            raise exc

    def _get_container_info(self) -> str:
        container_info = f'"{self.parent.name}"'
        if is_group(self.parent):
            container_info = self.parent.__class__.__name__

        return container_info

    def _ensure_unique_parent(self) -> str:
        """
        Ensure that parent is unique and give information if it isn't

        :return: empty string or warning info
        """
        info = ''
        if self.parent:
            parents_count = len(self.parent._find_elements())
            if parents_count > 1:
                info = f'\nWARNING: Located {parents_count} elements for {self._get_container_info()} container'

        return info

    def _get_cached_element(self, obj: Union[CoreElement, Element]) -> Union[None, SeleniumWebElement, AppiumWebElement]:
        """
        Get cached element from given object

        :param obj: CoreElement object
        :return: None, SeleniumWebElement, AppiumWebElement
        """
        return getattr(obj, '_cached_element', None)

    def _is_element_still_available(self, element: Union[None, SeleniumWebElement, AppiumWebElement]) -> bool:
        """
        Check is the element still available on page

        :param element: SeleniumWebElement, AppiumWebElement object
        :return: bool
        """
        if not element:
            return False

        return bool(safe_call(self.driver_wrapper.execute_script, 'return arguments[0];', element))
