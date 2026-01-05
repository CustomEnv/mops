from __future__ import annotations

from abc import ABC
from typing import Union, Any, List, Tuple, Optional, TYPE_CHECKING

from PIL.Image import Image
from appium.webdriver.extensions.location import Location

from mops.mixins.objects.box import Box
from mops.mixins.objects.scrolls import ScrollTo, ScrollTypes
from selenium.webdriver.remote.webelement import WebElement as SeleniumWebElement
from appium.webdriver.webelement import WebElement as AppiumWebElement
from playwright.sync_api import Locator as PlayWebElement

from mops.abstraction.mixin_abc import MixinABC
from mops.keyboard_keys import KeyboardKeys
from mops.mixins.objects.size import Size
from mops.utils.internal_utils import WAIT_EL, QUARTER_WAIT_EL

if TYPE_CHECKING:
    from mops.mixins.objects.locator import Locator
    from mops.base.element import Element


class ElementABC(MixinABC, ABC):

    locator: Union[Locator, str]
    name: str = ''
    parent: Union[Any, bool, None] = None
    wait: Optional[bool] = None

    @property
    def element(self) -> Union[SeleniumWebElement, AppiumWebElement, PlayWebElement]:
        """
        Returns a source element object, depending on the current driver in use.

        :return: :class:`selenium.webdriver.remote.webelement.WebElement` or\n
          :class:`appium.webdriver.webelement.WebElement` or\n
          :class:`playwright.sync_api.Locator`
        """
        raise NotImplementedError()

    @element.setter
    def element(self, base_element: Union[SeleniumWebElement, AppiumWebElement, PlayWebElement]):
        """
        Sets the source element object.

        :param base_element: :class:`selenium.webdriver.remote.webelement.WebElement` or\n
          :class:`appium.webdriver.webelement.WebElement` or\n
          :class:`playwright.sync_api.Locator`
        """
        raise NotImplementedError()

    @property
    def all_elements(self) -> Union[List[Element], List[Any]]:
        """
        Returns a list of all matching elements.

        :return: A list of wrapped :class:`Element` objects.
        """
        raise NotImplementedError()

    def click(self, *, force_wait: bool = True, **kwargs) -> Element:
        """
        Clicks on the element.

        :param force_wait: If :obj:`True`, waits for element visibility before clicking.
        :type force_wait: bool

        **Selenium/Appium:**

        Selenium Safari using js click instead.

        :param kwargs: compatibility arg for playwright

        **Playwright:**

        :param kwargs: `any kwargs params from source API <https://playwright.dev/python/docs/api/class-locator#locator-click>`_

        :return: :class:`Element`
        """
        raise NotImplementedError()

    def click_into_center(self, silent: bool = False) -> Element:
        """
        Clicks at the center of the element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def type_text(self, text: Union[str, KeyboardKeys], silent: bool = False) -> Element:
        """
        Types text into the element.

        :param text: The text to be typed or a keyboard key.
        :type text: str, :class:`KeyboardKeys`
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def type_slowly(self, text: str, sleep_gap: float = 0.05, silent: bool = False) -> Element:
        """
        Types text into the element slowly with a delay between keystrokes.

        :param text: The text to be typed.
        :type text: str
        :param sleep_gap: Delay between keystrokes in seconds.
        :type sleep_gap: float
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def clear_text(self, silent: bool = False) -> Element:
        """
        Clears the text of the element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def check(self) -> Element:
        """
        Checks the checkbox element.

        :return: :class:`Element`
        """
        raise NotImplementedError()

    def uncheck(self) -> Element:
        """
        Unchecks the checkbox element.

        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_visibility(
            self,
            *,
            timeout: int = WAIT_EL,
            silent: bool = False,
            continuous: Union[bool, int, float] = False,
    ) -> Element:
        """
        Waits until the element becomes visible.
         **Note:** The method requires the use of named arguments.

        A continuous visibility verification may be applied for given
        or default amount of time after the first condition is met.

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
        :param continuous: If :obj:`True`, a continuous visibility verification applied for another 2.5 seconds.
          An :obj:`int` or :obj:`float` modifies the continuous wait timeout.
        :type continuous: typing.Union[int, float, bool]
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_hidden(
            self,
            *,
            timeout: int = WAIT_EL,
            silent: bool = False,
            continuous: Union[bool, int, float] = False,
    ) -> Element:
        """
        Waits until the element becomes hidden.
         **Note:** The method requires the use of named arguments.

        A continuous invisibility verification may be applied for given
        or default amount of time after the first condition is met.

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
        :param continuous: If :obj:`True`, a continuous invisibility verification applied for another 2.5 seconds.
          An :obj:`int` or :obj:`float` modifies the continuous wait timeout.
        :type continuous: typing.Union[int, float, bool]
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_availability(self, *, timeout: int = WAIT_EL, silent: bool = False) -> Element:
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
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def save_screenshot(
            self,
            file_name: str,
            screenshot_base: Union[bytes, Image] = None,
            convert_type: str = None
    ) -> Image:
        """
        Saves a screenshot of the element.

        :param file_name: Path or filename for the screenshot.
        :type file_name: str
        :param screenshot_base: Screenshot binary or image to use (optional).
        :type screenshot_base: :obj:`bytes`, :class:`PIL.Image.Image`
        :param convert_type: Image conversion type before saving (optional).
        :type convert_type: str
        :return: :class:`PIL.Image.Image`
        """
        raise NotImplementedError()

    def hide(self, silent: bool = False) -> Element:
        """
        Make the element invisible by setting its opacity to 0.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def show(self, silent: bool = False) -> Element:
        """
        Make the element visible by setting its opacity to 1.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def execute_script(self, script: str, *args: Any) -> Any:
        """
        Executes a JavaScript script on the element.

        :param script: JavaScript code to be executed, referring to the element as ``arguments[0]``.
        :type script: str
        :param args: Any arguments to pass to the JavaScript.
        :type args: :obj:`typing.Any`
        :return: :obj:`typing.Any` result from the script.
        """
        raise NotImplementedError()

    def screenshot_image(self, screenshot_base: bytes = None) -> Image:
        """
        Returns a :class:`PIL.Image.Image` object representing the screenshot of the web element.
        Appium iOS: Take driver screenshot and crop manually element from it

        :param screenshot_base: Screenshot binary data (optional).
          If :obj:`None` is provided then takes a new screenshot
        :type screenshot_base: bytes
        :return: :class:`PIL.Image.Image`
        """
        raise NotImplementedError()

    @property
    def screenshot_base(self) -> bytes:
        """
        Returns the binary screenshot data of the element.

        :return: :class:`bytes` - screenshot binary
        """
        raise NotImplementedError()

    @property
    def text(self) -> str:
        """
        Returns the text of the element.

        :return: :class:`str` - element text
        """
        raise NotImplementedError()

    @property
    def inner_text(self) -> str:
        """
        Returns the inner text of the element.

        :return: :class:`str` - element inner text
        """
        raise NotImplementedError()

    @property
    def value(self) -> str:
        """
        Returns the value of the element.

        :return: :class:`str` - element value
        """
        raise NotImplementedError()

    def is_available(self) -> bool:
        """
        Checks if the element is available in DOM tree.

        :return: :class:`bool` - :obj:`True` if present in DOM
        """
        raise NotImplementedError()

    def is_displayed(self, silent: bool = False) -> bool:
        """
        Checks if the element is displayed.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        raise NotImplementedError()

    def is_hidden(self, silent: bool = False) -> bool:
        """
        Checks if the element is hidden.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        raise NotImplementedError()

    def get_attribute(self, attribute: str, silent: bool = False) -> str:
        """
        Retrieve a specific attribute from the current element.

        :param attribute: The name of the attribute to retrieve, such as 'value', 'innerText', 'textContent', etc.
        :type attribute: str
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`str` - The value of the specified attribute.
        """
        raise NotImplementedError()

    def get_all_texts(self, silent: bool = False) -> List[str]:
        """
        Retrieve text content from all matching elements.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`list` of :class:`str` - A list containing the text content of all matching elements.
        """
        raise NotImplementedError()

    def get_elements_count(self, silent: bool = False) -> int:
        """
        Get the count of matching elements.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`int` - The number of matching elements.
        """
        raise NotImplementedError()

    def get_rect(self) -> dict:
        """
        Retrieve the size and position of the element as a dictionary.

        :return: :class:`dict` - A dictionary {'x', 'y', 'width', 'height'} of the element.
        """
        raise NotImplementedError()

    @property
    def size(self) -> Size:
        """
        Get the size of the current element, including width and height.

        :return: :class:`.Size` - An object representing the element's dimensions.
        """
        raise NotImplementedError()

    @property
    def location(self) -> Location:
        """
        Get the location of the current element, including the x and y coordinates.

        :return: :class:`.Location` - An object representing the element's position.
        """
        raise NotImplementedError()

    def is_enabled(self, silent: bool = False) -> bool:
        """
        Check if the current element is enabled.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool` - :obj:`True` if the element is enabled, :obj:`False` otherwise.
        """
        raise NotImplementedError()

    def is_checked(self) -> bool:
        """
        Check if a checkbox or radio button is selected.

        :return: :class:`bool` - :obj:`True` if the checkbox or radio button is checked, :obj:`False` otherwise.
        """
        raise NotImplementedError()

    def hover(self, silent: bool = False) -> Element:
        """
        Hover the mouse over the current element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def hover_outside(self, x: int = 0, y: int = -5) -> Element:
        """
        Hover the mouse outside the current element, by default 5px above it.

        :param x: Horizontal offset from the element to hover.
        :type x: int
        :param y: Vertical offset from the element to hover.
        :type y: int
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def click_outside(self, x: int = -5, y: int = -5) -> Element:
        """
        Perform a click outside the current element, by default 5px left and above it.

        :param x: Horizontal offset from the element to click.
        :type x: int
        :param y: Vertical offset from the element to click.
        :type y: int
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def click_in_alert(self) -> Element:
        """
        Perform a click on an element inside an alert box (Mobile only).
        **Note:** Automatically switches to native context of the browser.

        :return: :class:`Element`
        """
        raise NotImplementedError()

    def set_text(self, text: str, silent: bool = False) -> Element:
        """
        Clear the current input field and type the provided text.

        :param text: The text to enter into the element.
        :type text: str
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def send_keyboard_action(self, action: Union[str, KeyboardKeys]) -> Element:
        """
        Send a keyboard action to the current element (e.g., press a key or shortcut).

        :param action: The keyboard action to perform.
        :type action: str or :class:`KeyboardKeys`
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_elements_count(
            self,
            expected_count: int,
            *,
            timeout: Union[int, float] = WAIT_EL,
            silent: bool = False
    ) -> Element:
        """
        Wait until the number of matching elements equals the expected count.

        **Note:** The method requires the use of named arguments except ``expected_count``.

        **Selenium & Playwright:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param expected_count: The expected number of elements.
        :type expected_count: int
        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`WAIT_EL`.
        :type timeout: typing.Union[int, float]
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_for_text(
            self,
            expected_text: Optional[str] = None,
            *,
            timeout: Union[int, float] = WAIT_EL,
            silent: bool = False
    ) -> Element:
        """
        Wait for the presence of a specific text in the current element, or for any non-empty text.

        **Note:** The method requires the use of named arguments except ``expected_text``.

        **Selenium & Playwright:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param expected_text: The text to wait for. :obj:`None` - any text; :class:`str` - expected text.
        :type expected_text: typing.Optional[str]
        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`WAIT_EL`.
        :type timeout: typing.Union[int, float]
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_for_value(
            self,
            expected_value: Optional[str] = None,
            *,
            timeout: Union[int, float] = WAIT_EL,
            silent: bool = False
    ) -> Element:
        """
        Wait for a specific value in the current element, or for any non-empty value.

        **Note:** The method requires the use of named arguments except ``expected_value``.

        **Selenium & Playwright:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param expected_value: The value to waiting for. :obj:`None` - any value; :class:`str` - expected value.
        :type expected_value: typing.Optional[str]
        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`WAIT_EL`.
        :type timeout: typing.Union[int, float]
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_visibility_without_error(
            self,
            *,
            timeout: Union[int, float] = QUARTER_WAIT_EL,
            silent: bool = False,
            continuous: Union[bool, int, float] = False,
    ) -> Element:
        """
        Wait for the element to become visible, without raising an error if it does not.
         **Note:** The method requires the use of named arguments.

        A continuous visibility verification may be applied for given
        or default amount of time after the first condition is met.

        **Selenium & Playwright:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`QUARTER_WAIT_EL`.
        :type timeout: typing.Union[int, float]
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :param continuous: If :obj:`True`, a continuous visibility verification applied for another 2.5 seconds.
          An :obj:`int` or :obj:`float` modifies the continuous wait timeout.
        :type continuous: typing.Union[int, float, bool]
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_hidden_without_error(
            self,
            *,
            timeout: Union[int, float] = QUARTER_WAIT_EL,
            silent: bool = False,
            continuous: Union[bool, int, float] = False,
    ) -> Element:
        """
        Wait for the element to become hidden, without raising an error if it does not.
         **Note:** The method requires the use of named arguments.

        A continuous invisibility verification may be applied for given
        or default amount of time after the first condition is met.

        **Selenium & Playwright:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`QUARTER_WAIT_EL`.
        :type timeout: typing.Union[int, float]
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :param continuous: If :obj:`True`, a continuous invisibility verification applied for another 2.5 seconds.
          An :obj:`int` or :obj:`float` modifies the continuous wait timeout.
        :type continuous: typing.Union[int, float, bool]
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_enabled(self, *, timeout: Union[int, float] = WAIT_EL, silent: bool = False) -> Element:
        """
        Wait for the element to become enabled and/or clickable.

        **Note:** The method requires the use of named arguments.

        **Selenium & Playwright:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`WAIT_EL`.
        :type timeout: typing.Union[int, float]
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_disabled(self, *, timeout: Union[int, float] = WAIT_EL, silent: bool = False) -> Element:
        """
        Wait for the element to become disabled.

        **Note:** The method requires the use of named arguments.

        **Selenium & Playwright:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`WAIT_EL`.
        :type timeout: [int, float]
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def wait_for_size(
            self,
            expected_size: Size,
            *,
            timeout: Union[int, float] = WAIT_EL,
            silent: bool = False
    ) -> Element:
        """
        Wait until element size will be equal to given :class:`.Size` object

        **Note:** The method requires the use of named arguments except ``expected_size``.

        **Selenium & Playwright:**

        - Applied :func:`wait_condition` decorator integrates a 0.1 seconds delay for each iteration
          during the waiting process.

        **Appium:**

        - Applied :func:`wait_condition` decorator integrates an exponential delay
          (starting at 0.1 seconds, up to a maximum of 1.6 seconds) which increases
          with each iteration during the waiting process.

        :param expected_size: expected element size
        :type expected_size: :class:`.Size`
        :param timeout: The maximum time to wait for the condition (in seconds). Default: :obj:`WAIT_EL`.
        :type timeout: typing.Union[int, float]
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def is_visible(self, check_displaying: bool = True, silent: bool = False) -> bool:
        """
        Checks is the current element's top-left corner or bottom-right corner is visible on the screen.

        :param check_displaying: If :obj:`True`, the :func:`is_displayed` method will be called to further verify
          visibility. The check will stop if this method returns :obj:`False`.
        :type check_displaying: bool
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        raise NotImplementedError()

    def is_fully_visible(self, check_displaying: bool = True, silent: bool = False) -> bool:
        """
        Check is current element top left corner and bottom right corner visible on current screen

        :param check_displaying: If :obj:`True`, the :func:`is_displayed` method will be called to further verify
          visibility. The check will stop if this method returns :obj:`False`.
        :type check_displaying: bool
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        raise NotImplementedError()

    def scroll_into_view(
            self,
            block: ScrollTo = ScrollTo.CENTER,
            behavior: ScrollTypes = ScrollTypes.INSTANT,
            sleep: Union[int, float] = 0,
            silent: bool = False,
    ) -> Element:
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
        :return: :class:`Element`
        """
        raise NotImplementedError()

    def assert_screenshot(
            self,
            filename: str = '',
            test_name: str = '',
            name_suffix: str = '',
            threshold: Union[int, float] = None,
            delay: Union[int, float] = None,
            scroll: bool = False,
            remove: Union[Element, List[Element]] = None,
            fill_background: Union[str, bool] = False,
            cut_box: Box = None,
            hide: Union[Element, List[Element]] = None,
    ) -> None:
        """
        Asserts that the given screenshot matches the currently taken screenshot.

        :param filename: The full name of the screenshot file.
          If empty - filename will be generated based on test name & :class:`Element` ``name`` argument & platform.
        :type filename: str
        :param test_name: The custom test name for generated filename.
          If empty - it will be determined automatically.
        :type test_name: str
        :param name_suffix: A suffix to add to the filename.
          Useful for distinguishing between positive and negative cases for the same :class:`Element` during one test.
        :type name_suffix: str
        :param threshold: The acceptable threshold for comparing screenshots.
          If :obj:`None` - takes default threshold or calculate its automatically based on screenshot size.
        :type threshold: typing.Optional[int, float]
        :param delay: The delay in seconds before taking the screenshot.
          If :obj:`None` - takes default delay.
        :type delay: typing.Optional[int, float]
        :param scroll: Whether to scroll to the element before taking the screenshot.
        :type scroll: bool
        :param remove: :class:`Element` to remove from the screenshot.
          Can be a single element or a list of elements.
        :type remove: typing.Optional[Element or typing.List[Element]]
        :param fill_background: The color to fill the background.
          If :obj:`True`, uses a default color (black). If a :class:`str`, uses the specified color.
        :type fill_background: typing.Optional[str or bool]
        :param cut_box: A :class:`.Box` specifying a region to cut from the screenshot.
            If :obj:`None`, no region is cut.
        :type cut_box: typing.Optional[Box]
        :param hide: :class:`Element` to hide in the screenshot.
          Can be a single element or a list of elements.
        :type hide: typing.Optional[Element or typing.List[Element]]
        :return: :obj:`None`
        """
        raise NotImplementedError()

    def soft_assert_screenshot(
            self,
            filename: str = '',
            test_name: str = '',
            name_suffix: str = '',
            threshold: Union[int, float] = None,
            delay: Union[int, float] = None,
            scroll: bool = False,
            remove: Union[Element, List[Element]] = None,
            fill_background: Union[str, bool] = False,
            cut_box: Box = None,
            hide: Union[Element, List[Element]] = None,
    ) -> Tuple[bool, str]:
        """
        Compares the currently taken screenshot to the expected screenshot and returns a result.

        :param filename: The full name of the screenshot file.
          If empty - filename will be generated based on test name & :class:`Element` ``name`` argument & platform.
        :type filename: str
        :param test_name: The custom test name for generated filename.
          If empty - it will be determined automatically.
        :type test_name: str
        :param name_suffix: A suffix to add to the filename.
          Useful for distinguishing between positive and negative cases for the same :class:`Element` during one test.
        :type name_suffix: str
        :param threshold: The acceptable threshold for comparing screenshots.
          If :obj:`None` - takes default threshold or calculate its automatically based on screenshot size.
        :type threshold: typing.Optional[int, float]
        :param delay: The delay in seconds before taking the screenshot.
          If :obj:`None` - takes default delay.
        :type delay: typing.Optional[int, float]
        :param scroll: Whether to scroll to the element before taking the screenshot.
        :type scroll: bool
        :param remove: :class:`Element` to remove from the screenshot.
        :type remove: typing.Optional[Element or typing.List[Element]]
        :param fill_background: The color to fill the background.
          If :obj:`True`, uses a default color (black). If a :class:`str`, uses the specified color.
        :type fill_background: typing.Optional[str or bool]
        :param cut_box: A :class:`.Box` specifying a region to cut from the screenshot.
            If :obj:`None`, no region is cut.
        :type cut_box: typing.Optional[Box]
        :param hide: :class:`Element` to hide in the screenshot.
          Can be a single element or a list of elements.
        :return: :class:`typing.Tuple` (:class:`bool`, :class:`str`) - result state and result message
        """
        raise NotImplementedError()

    def get_element_info(self, element: Optional[Element] = None) -> str:
        """
        Retrieves detailed logging information for the specified element.

        :param element: The :class:`Element` for which to collect logging data.
          If :obj:`None`, logging data for the ``parent`` element is used.
        :type element: :class:`Element` or :obj:`None`
        :return: :class:`str` - A string containing the log data.
        """
        raise NotImplementedError()

    def _get_all_elements(self, sources: Union[tuple, list]) -> List[Element]:
        """
        Retrieves all wrapped elements from the given sources.

        :param sources: A list or tuple of source objects
        :type sources: tuple or list
        :return: A list of wrapped :class:`Element` objects.
        """
        raise NotImplementedError()
