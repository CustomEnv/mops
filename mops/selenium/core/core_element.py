from __future__ import annotations

import time
from abc import ABC
from typing import Union, List, Any, Callable, TYPE_CHECKING

from PIL import Image

from mops.mixins.internal_mixin import get_element_info
from mops.mixins.objects.wait_result import Result
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver
from selenium.webdriver.remote.webelement import WebElement as SeleniumWebElement
from appium.webdriver.webelement import WebElement as AppiumWebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    InvalidArgumentException as SeleniumInvalidArgumentException,
    InvalidSelectorException as SeleniumInvalidSelectorException,
    NoSuchElementException as SeleniumNoSuchElementException,
    ElementNotInteractableException as SeleniumElementNotInteractableException,
    ElementClickInterceptedException as SeleniumElementClickInterceptedException,
    StaleElementReferenceException as SeleniumStaleElementReferenceException,
)
from mops.abstraction.element_abc import ElementABC
from mops.selenium.sel_utils import ActionChains
from mops.js_scripts import get_element_size_js, get_element_position_on_screen_js
from mops.keyboard_keys import KeyboardKeys
from mops.mixins.objects.location import Location
from mops.mixins.objects.scrolls import ScrollTo, ScrollTypes, scroll_into_view_blocks
from mops.mixins.objects.size import Size
from mops.shared_utils import cut_log_data, _scaled_screenshot
from mops.utils.internal_utils import WAIT_EL, safe_call, get_dict, HALF_WAIT_EL, wait_condition, is_group, retry
from mops.exceptions import (
    TimeoutException,
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

        self.element = self._get_element(force_wait=force_wait)

        selenium_exc_msg = None
        start_time = time.time()
        while time.time() - start_time < HALF_WAIT_EL:
            try:
                element = self.wait_enabled(silent=True).element
                element.click()
                return self
            except (
                    SeleniumElementNotInteractableException,
                    SeleniumElementClickInterceptedException,
                    SeleniumStaleElementReferenceException,
            ) as exc:
                selenium_exc_msg = exc.msg
            finally:
                self.element = None

        raise ElementNotInteractableException(
            f'Element "{self.name}" not interactable after {HALF_WAIT_EL} seconds. {self.get_element_info()}. '
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
        self.element = self._get_element(wait=self.wait_availability)

        try:
            if not self.is_checked():
                self.click(with_wait=False)
        finally:
            self.element = None

        return self

    def uncheck(self) -> CoreElement:
        """
        Unchecks the checkbox element.

        :return: :class:`CoreElement`
        """
        self.element = self._get_element(wait=self.wait_availability)

        try:
            if self.is_checked():
                self.click(with_wait=False)
        finally:
            self.element = None

        return self

    # Element waits

    @wait_condition
    def wait_visibility(self, *, timeout: int = WAIT_EL, silent: bool = False) -> CoreElement:
        """
        Waits until the element becomes visible.
        **Note:** The method requires the use of named arguments.

        **Selenium:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`WAIT_EL`.
        :type timeout: int
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`CoreElement`
        """
        return Result(  # noqa
            execution_result=self.is_displayed(silent=True),
            log=f'Wait until "{self.name}" becomes visible',
            exc=TimeoutException(f'"{self.name}" not visible', info=self)
        )

    @wait_condition
    def wait_hidden(self, *, timeout: int = WAIT_EL, silent: bool = False) -> CoreElement:
        """
        Waits until the element becomes hidden.
        **Note:** The method requires the use of named arguments.

        **Selenium:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`WAIT_EL`.
        :type timeout: int
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`CoreElement`
        """
        return Result(  # noqa
            execution_result=self.is_hidden(silent=True),
            log=f'Wait until "{self.name}" becomes hidden',
            exc=TimeoutException(f'"{self.name}" still visible', info=self),
        )

    @wait_condition
    def wait_availability(self, *, timeout: int = WAIT_EL, silent: bool = False) -> CoreElement:
        """
        Waits until the element becomes available in DOM tree. \n
        **Note:** The method requires the use of named arguments.

        **Selenium:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`WAIT_EL`.
        :type timeout: int
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`CoreElement`
        """
        return Result(  # noqa
            execution_result=self.is_available(),
            log=f'Wait until presence of "{self.name}"',
            exc=TimeoutException(f'"{self.name}" not available in DOM', info=self),
        )

    # Element state

    def scroll_into_view(
            self,
            block: ScrollTo = ScrollTo.CENTER,
            behavior: ScrollTypes = ScrollTypes.INSTANT,
            sleep: Union[int, float] = 0,
            silent: bool = False,
    ) -> CoreElement:
        """
        Scrolls the element into view using a JavaScript script.

        :param block: The scrolling block alignment. One of the :class:`.ScrollTo` options.
        :type block: ScrollTo
        :param behavior: The scrolling behavior. One of the :class:`.ScrollTypes` options.
        :type behavior: ScrollTypes
        :param sleep: Delay in seconds after scrolling. Can be an integer or a float.
        :type sleep: typing.Union[int, float]
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`CoreElement`
        """
        if not silent:
            self.log(f'Scroll element "{self.name}" into view')

        assert block in scroll_into_view_blocks, f'Provide one of {scroll_into_view_blocks} option in `block` argument'

        self.execute_script(f'arguments[0].scrollIntoView({{block: "{block}", behavior: "{behavior}"}});')

        if sleep:
            time.sleep(sleep)

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
        screenshot_base = screenshot_base if screenshot_base else self.screenshot_base
        return _scaled_screenshot(screenshot_base, self.size.width)

    @property
    def screenshot_base(self) -> bytes:
        """
        Returns the binary screenshot data of the element.

        :return: :class:`bytes` - screenshot binary
        """
        return self.element.screenshot_as_png

    @property
    @retry(SeleniumStaleElementReferenceException)
    def text(self) -> str:
        """
        Returns the text of the element.

        :return: :class:`str` - element text
        """
        element = self._get_element(wait=self.wait_availability)

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
        try:
            element = safe_call(self._find_element, wait_parent=False)
        except SeleniumInvalidSelectorException as exc:
            raise InvalidSelectorException(exc.msg)

        return bool(element)

    def is_displayed(self, silent: bool = False) -> bool:
        """
        Checks if the element is displayed.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        if not silent:
            self.log(f'Check displaying of "{self.name}"')

        is_displayed = self.is_available()

        if is_displayed:
            is_displayed = safe_call(self._cached_element.is_displayed)

        return is_displayed

    def is_hidden(self, silent: bool = False) -> bool:
        """
        Checks if the element is hidden.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        if not silent:
            self.log(f'Check invisibility of "{self.name}"')

        return not self.is_displayed(silent=True)

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
    def size(self) -> Size:
        """
        Get the size of the current element, including width and height.

        :return: :class:`.Size` - An object representing the element's dimensions.
        """
        return Size(**self.execute_script(get_element_size_js))

    @property
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
        return self._get_element(wait=self.wait_availability).is_selected()

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

    def _get_element(self, wait: Union[bool, Callable] = True, force_wait: bool = False) -> SeleniumWebElement:
        """
        Get selenium element from driver or parent element

        :param wait: wait strategy for element and/or element parent before grab
        :param force_wait: force wait for some element
        :return: SeleniumWebElement
        """
        element = self._element

        if wait is True:
            wait = self.wait_visibility

        if not element:

            # Try to get element instantly without wait. Skipped if force_wait given
            if not force_wait:
                element = safe_call(self._find_element, wait_parent=False)

            # Wait for element if it is not found instantly
            if (not element and wait) or force_wait:
                element = self._get_cached_element(safe_call(wait, silent=True))

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

    def _get_base(self, wait: Union[bool, Callable] = True) -> Union[SeleniumWebDriver, SeleniumWebElement]:
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
            base = self.parent._get_element(wait=wait)

        return base

    def _find_element(self, wait_parent: bool = False) -> Union[SeleniumWebElement, AppiumWebElement]:
        """
        Find selenium/appium element

        :param wait_parent: wait for base(parent) element
        :return: SeleniumWebElement or AppiumWebElement
        """
        base = self._get_base(wait=wait_parent)
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
        base = self._get_base(wait=wait_parent)
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
