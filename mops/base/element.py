from __future__ import annotations

import time
from copy import copy
from typing import Union, List, Type, Tuple, Optional, TYPE_CHECKING

from PIL.Image import Image

from mops.mixins.objects.scrolls import ScrollTo, ScrollTypes, scroll_into_view_blocks
from mops.mixins.objects.visual_comaprison_mixin import hide_before_screenshot, reveal_after_screenshot
from mops.mixins.objects.wait_result import Result
from playwright.sync_api import Page as PlaywrightDriver
from appium.webdriver.webdriver import WebDriver as AppiumDriver
from selenium.common import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumDriver

from mops.abstraction.element_abc import ElementABC
from mops.base.driver_wrapper import DriverWrapper
from mops.exceptions import *
from mops.playwright.play_element import PlayElement
from mops.selenium.elements.mobile_element import MobileElement
from mops.selenium.elements.web_element import WebElement
from mops.mixins.driver_mixin import get_driver_wrapper_from_object, DriverMixin
from mops.mixins.internal_mixin import InternalMixin, get_element_info
from mops.mixins.objects.box import Box
from mops.mixins.objects.locator import Locator
from mops.mixins.objects.size import Size
from mops.utils.logs import Logging, LogLevel
from mops.utils.previous_object_driver import PreviousObjectDriver, set_instance_frame
from mops.visual_comparison import VisualComparison
from mops.keyboard_keys import KeyboardKeys
from mops.utils.internal_utils import (
    WAIT_EL,
    is_target_on_screen,
    initialize_objects,
    get_child_elements_with_names,
    safe_getattribute,
    set_parent_for_attr,
    is_page,
    QUARTER_WAIT_EL,
)
from mops.utils.decorators import wait_condition, wait_continuous

if TYPE_CHECKING:
    from mops.base.group import Group


class Element(DriverMixin, InternalMixin, Logging, ElementABC):
    """
    Represents a UI element that serves as a central component for interaction.

    The :class:`Element` class is designed to be used within :class:`.Page` or :class:`.Group` objects.

    It dynamically adapts to different driver types (Playwright, Appium, Selenium)
    and provides a unified interface for UI interactions.
    """

    _object = 'element'
    _base_cls: Type[PlayElement, MobileElement, WebElement]
    driver_wrapper: DriverWrapper

    def __new__(cls, *args, **kwargs):
        instance = super(Element, cls).__new__(cls)
        set_instance_frame(instance)
        return instance

    def __repr__(self):
        return self._repr_builder()

    def __call__(self, driver_wrapper: DriverWrapper = None):
        self.__full_init__(driver_wrapper=get_driver_wrapper_from_object(driver_wrapper))
        return self

    def __getattribute__(self, item):
        if 'element' in item and not safe_getattribute(self, '_initialized'):
            raise NotInitializedException(
                f'{repr(self)} object is not initialized. '
                'Try to initialize base object first or call it directly as a method'
            )

        return safe_getattribute(self, item)

    def __init__(
            self,
            locator: Union[Locator, str],
            name: str = '',
            parent: Union[Group, Element, bool] = None,
            wait: Optional[bool] = None,
            driver_wrapper: Union[DriverWrapper, Any] = None,
    ):
        """
        Initializes an Element based on the current driver.

        If no driver is available, initialization is skipped and will be handled later in a Page or Group.

        :param locator: The element's locator. `.LocatorType` is optional.
        :type locator: typing.Union[Locator, str]
        :param name: The name of the element, used for logging and identification purposes.
        :type name: str
        :param parent: The parent of the element. Provide :obj:`False` to skip association.
        :type parent: typing.Union[Group, Element, bool]
        :param wait: If `True`, the element will be checked in
         `wait_page_loaded` and `is_page_opened` methods of `Page`.
        :type wait: typing.Optional[bool]
        :param driver_wrapper: The :class:`.DriverWrapper` instance or
         an object containing it to be used for this element.
        :type driver_wrapper: typing.Union[DriverWrapper, typing.Any]
        """
        self._validate_inheritance()

        if parent:
            if not isinstance(parent, (bool, Element)):
                error = (f'The given "parent" arg of "{self.name}" should take an Element/Group '
                         f'object or False for skip. Get {parent}')
                raise ValueError(error)

        self.locator = locator
        self.name = name if name else locator
        self.parent = parent
        self.wait = wait
        self.driver_wrapper = get_driver_wrapper_from_object(driver_wrapper)

        self._init_locals = getattr(self, '_init_locals', locals())
        self._safe_setter('__base_obj_id', id(self))
        self._initialized = False

        if self.driver_wrapper:
            self.__full_init__(driver_wrapper)

    def __full_init__(self, driver_wrapper: Any = None):
        self._driver_wrapper_given = bool(driver_wrapper)

        if self._driver_wrapper_given and driver_wrapper != self.driver_wrapper:
            self.driver_wrapper = get_driver_wrapper_from_object(driver_wrapper)

        self._modify_object()
        self._modify_children()

        if not self._initialized:
            self.__init_base_class__()

    def __init_base_class__(self) -> None:
        """
        Initialise base class according to current driver, and set his methods

        :return: None
        """
        if isinstance(self.driver, PlaywrightDriver):
            self._base_cls = PlayElement
        elif isinstance(self.driver, AppiumDriver):
            self._base_cls = MobileElement
        elif isinstance(self.driver, SeleniumDriver):
            self._base_cls = WebElement
        else:
            raise DriverWrapperException(f'Cant specify {self.__class__.__name__}')

        self._set_static(self._base_cls)
        self._base_cls.__init__(self)
        self._initialized = True

    # Following methods works same for both Selenium/Appium and Playwright APIs using internal methods

    # Elements interaction

    def set_text(self, text: str, silent: bool = False) -> Element:
        """
        Clear the current input field and type the provided text.

        :param text: The text to enter into the element.
        :type text: str
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        if not silent:
            self.log(f'Set text in "{self.name}"')

        self.clear_text(silent=True).type_text(text, silent=True)
        return self

    def send_keyboard_action(self, action: Union[str, KeyboardKeys]) -> Element:
        """
        Send a keyboard action to the current element (e.g., press a key or shortcut).

        :param action: The keyboard action to perform.
        :type action: str or :class:`KeyboardKeys`
        :return: :class:`Element`
        """
        if self.driver_wrapper.is_playwright:
            self.click()
            self.driver.keyboard.press(action)
        else:
            self.type_text(action)

        return self

    # Elements waits

    @wait_continuous
    @wait_condition
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
        return Result(  # noqa
            execution_result=self.is_displayed(silent=True),
            log=f'Wait until "{self.name}" becomes visible',
            exc=TimeoutException(f'"{self.name}" not visible', info=self)
        )

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
        if not silent:
            strategy = 'continuous visible' if continuous else 'hidden'
            self.log(f'Wait until "{self.name}" becomes {strategy} without error exception')

        try:
            self.wait_visibility(timeout=timeout, silent=True, continuous=continuous)
        except (TimeoutException, WebDriverException, ContinuousWaitException) as exception:
            if not silent:
                self.log(f'Ignored exception: "{exception.msg}"')
        return self

    @wait_continuous
    @wait_condition
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
        return Result(  # noqa
            execution_result=self.is_hidden(silent=True),
            log=f'Wait until "{self.name}" becomes hidden',
            exc=TimeoutException(f'"{self.name}" still visible', info=self),
        )

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
        if not silent:
            strategy = 'continuous hidden' if continuous else 'hidden'
            self.log(f'Wait until "{self.name}" becomes {strategy} without error exception')

        try:
            self.wait_hidden(timeout=timeout, silent=silent, continuous=continuous)
        except (TimeoutException, WebDriverException, ContinuousWaitException) as exception:
            if not silent:
                self.log(f'Ignored exception: "{exception.msg}"')
        return self

    @wait_condition
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
        return Result(  # noqa
            execution_result=self.is_available(),
            log=f'Wait until presence of "{self.name}"',
            exc=TimeoutException(f'"{self.name}" not available in DOM', info=self),
        )

    @wait_condition
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
        actual_text = self.text

        if expected_text is not None:
            result = actual_text == expected_text
            error = f'Not expected text for "{self.name}"'
            log_msg = f'Wait until text of "{self.name}" will be equal to "{expected_text}"'
        else:
            result = actual_text
            error = f'Text of "{self.name}" is empty'
            log_msg = f'Wait for any text of "{self.name}"'

        return Result(result, log_msg, UnexpectedTextException(error, actual_text, expected_text))  # noqa

    @wait_condition
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
        actual_value = self.value

        if expected_value is not None:
            result = actual_value == expected_value
            error = f'Not expected value for "{self.name}"'
            log_msg = f'Wait until value of "{self.name}" will be equal to "{expected_value}"'
        else:
            result = actual_value
            error = f'Value of "{self.name}" is empty'
            log_msg = f'Wait for any value inside "{self.name}"'

        return Result(result, log_msg, UnexpectedValueException(error, actual_value, expected_value))  # noqa

    @wait_condition
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
        return Result(  # noqa
            execution_result=self.is_enabled(silent=True),
            log=f'Wait until "{self.name}" becomes enabled',
            exc=TimeoutException(f'"{self.name}" is not enabled', info=self),
        )

    @wait_condition
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
        return Result(  # noqa
            execution_result=not self.is_enabled(silent=True),
            log=f'Wait until "{self.name}" becomes disabled',
            exc=TimeoutException(f'"{self.name}" is not disabled', info=self),
        )

    @wait_condition
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
        actual = self.size
        is_height_equal = actual.height == expected_size.height if expected_size.height is not None else True
        is_width_equal = actual.width == expected_size.width if expected_size.width is not None else True
        return Result(  # noqa
            execution_result=is_height_equal and is_width_equal,
            log=f'Wait until "{self.name}" size will be equal to {expected_size}',
            exc=UnexpectedElementSizeException(f'Unexpected size for "{self.name}"', actual, expected_size),
        )

    @wait_condition
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
        actual_count = self.get_elements_count(silent=True)
        error_msg = f'Unexpected elements count of "{self.name}"'
        return Result(  # noqa
            execution_result=actual_count == expected_count,
            log=f'Wait until elements count of "{self.name}" will be equal to "{expected_count}"',
            exc=UnexpectedElementsCountException(error_msg, actual_count, expected_count),
        )


    @property
    def all_elements(self) -> Union[List[Element], List[Any]]:
        """
        Returns a list of all matching elements.

        :return: A list of wrapped :class:`Element` objects.
        """
        if getattr(self, '_wrapped', None):
            raise RecursionError(f'all_elements property already used for {self.name}')

        return self._base_cls.all_elements.fget(self)

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
        if not silent:
            self.log(f'Check visibility of "{self.name}"')

        is_visible = True

        if check_displaying:
            is_visible = self.is_displayed()

        if is_visible:
            rect, window_size = self.get_rect(), self.driver_wrapper.get_inner_window_size()
            x_end, y_end = rect['x'] + rect['width'], rect['y'] + rect['height']
            is_start_visible = is_target_on_screen(x=rect['x'], y=rect['y'], possible_range=window_size)
            is_end_visible = is_target_on_screen(x=x_end, y=y_end, possible_range=window_size)
            is_visible = is_start_visible or is_end_visible

        return is_visible

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
        if not silent:
            self.log(f'Check fully visibility of "{self.name}"')

        is_visible = True

        if check_displaying:
            is_visible = self.is_displayed()

        if is_visible:
            rect, window_size = self.get_rect(), self.driver_wrapper.get_inner_window_size()
            x_end, y_end = rect['x'] + rect['width'], rect['y'] + rect['height']
            is_start_visible = is_target_on_screen(x=rect['x'], y=rect['y'], possible_range=window_size)
            is_end_visible = is_target_on_screen(x=x_end, y=y_end, possible_range=window_size)
            is_visible = is_start_visible and is_end_visible

        return is_visible

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
        if not silent:
            self.log(f'Scroll element "{self.name}" into view')

        if block not in scroll_into_view_blocks:
            message = f'Provide one of {scroll_into_view_blocks} option in `block` argument'
            raise UnsuitableArgumentsException(message)

        self.execute_script(
            'arguments[0].scrollIntoView({block: arguments[1], behavior: arguments[2]});',
            block, behavior
        )

        if sleep:
            time.sleep(sleep)

        return self

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
        self.log(f'Save screenshot of {self.name}')

        image_object = screenshot_base
        if isinstance(screenshot_base, bytes) or screenshot_base is None:
            image_object = self._base_cls.screenshot_image(self, screenshot_base)

        if convert_type:
            image_object = image_object.convert(convert_type)

        image_object.save(file_name)

        return image_object

    def hide(self, silent: bool = False) -> Element:
        """
        Make the element invisible by setting its opacity to 0.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        if not silent:
            self.log(f'Hiding element "{self.name}"')

        self.execute_script('arguments[0].style.opacity = "0";')
        return self

    def show(self, silent: bool = False) -> Element:
        """
        Make the element visible by setting its opacity to 1.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`Element`
        """
        if not silent:
            self.log(f'Showing element "{self.name}"')

        self.execute_script('arguments[0].style.opacity = "1";')
        return self

    def execute_script(self, script: str, *args: Any) -> Any:
        """
        Executes a JavaScript script on the element.

        :param script: JavaScript code to be executed, referring to the element as ``arguments[0]``.
        :type script: str
        :param args: Any arguments to pass to the JavaScript.
        :type args: :obj:`typing.Any`
        :return: :obj:`typing.Any` result from the script.
        """
        return self.driver_wrapper.execute_script(script, *[self, *[arg for arg in args]])

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
        delay = delay or VisualComparison.default_delay
        remove = [remove] if type(remove) is not list and remove else remove

        if scroll:
            self.scroll_into_view()

        hide_before_screenshot(hide, is_optional=False, dw=self.driver_wrapper)
        self.driver_wrapper.wait(delay)
        hide_before_screenshot(VisualComparison.always_hide, is_optional=True, dw=self.driver_wrapper)

        VisualComparison(self.driver_wrapper, self).assert_screenshot(
            filename=filename, test_name=test_name, name_suffix=name_suffix, threshold=threshold,
            remove=remove, fill_background=fill_background, cut_box=cut_box
        )

        reveal_after_screenshot(VisualComparison.always_hide, dw=self.driver_wrapper)

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
        try:
            self.assert_screenshot(
                filename, test_name, name_suffix, threshold, delay, scroll, remove, fill_background, cut_box, hide
            )
        except AssertionError as exc:
            exc = str(exc)
            self.log(exc, level=LogLevel.ERROR)
            return False, exc

        return True, f'No visual mismatch found for {self.name}'

    def get_element_info(self, element: Optional[Element] = None) -> str:
        """
        Retrieves detailed logging information for the specified element.

        :param element: The :class:`Element` for which to collect logging data.
          If :obj:`None`, logging data for the ``parent`` element is used.
        :type element: :class:`Element` or :obj:`None`
        :return: :class:`str` - A string containing the log data.
        """
        element = element if element else self
        return get_element_info(element)

    def _get_all_elements(self, sources: Union[tuple, list]) -> List[Any]:
        """
        Retrieves all wrapped elements from the given sources.

        :param sources: A list or tuple of source objects
        :type sources: tuple or list
        :return: A list of wrapped :class:`Element` objects.
        """
        wrapped_elements = []

        for element in sources:
            wrapped_object: Any = copy(self)
            wrapped_object.element = element
            wrapped_object._wrapped = True
            set_parent_for_attr(wrapped_object, Element, with_copy=True)
            wrapped_elements.append(wrapped_object)

        return wrapped_elements

    def _modify_children(self):
        """
        Initializing of attributes with  type == Element.
        Required for classes with base == Element.
        """
        initialize_objects(self, get_child_elements_with_names(self, Element), Element)

    def _modify_object(self):
        """
        Modify current object if driver_wrapper is not given. Required for Page that placed into functions:
        - sets driver from previous object
        """
        if not self._driver_wrapper_given:
            PreviousObjectDriver().set_driver_from_previous_object(self)

    def _validate_inheritance(self):
        cls = self.__class__
        mro = cls.__mro__

        for item in mro:
            if is_page(item):
                raise TypeError(
                    f"You cannot make an inheritance for {cls.__name__} from both Element/Group and Page objects")
