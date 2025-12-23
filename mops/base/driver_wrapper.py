from __future__ import annotations

from typing import Union, Type, List, Tuple, TYPE_CHECKING

from PIL import Image
from appium.webdriver.webdriver import WebDriver as AppiumDriver
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumDriver
from playwright.sync_api import (
    Page as PlaywrightDriver,
    Browser as PlaywrightBrowser,
    BrowserContext as PlaywrightContext,
)

from mops.mixins.objects.box import Box
from mops.mixins.objects.driver import Driver
from mops.mixins.objects.visual_comaprison_mixin import hide_before_screenshot, reveal_after_screenshot
from mops.visual_comparison import VisualComparison
from mops.abstraction.driver_wrapper_abc import DriverWrapperABC
from mops.playwright.play_driver import PlayDriver
from mops.selenium.driver.mobile_driver import MobileDriver
from mops.selenium.driver.web_driver import WebDriver
from mops.exceptions import DriverWrapperException
from mops.mixins.internal_mixin import InternalMixin
from mops.utils.internal_utils import get_attributes_from_object, get_child_elements_with_names
from mops.utils.logs import Logging, LogLevel


if TYPE_CHECKING:
    from mops.base.element import Element


class DriverWrapperSessions:
    all_sessions: List[DriverWrapper] = []

    @classmethod
    def add_session(cls, driver_wrapper: DriverWrapper) -> None:
        """
        Adds a :obj:`.DriverWrapper` object to the session pool.

        :param driver_wrapper: The :obj:`.DriverWrapper` instance to add to the pool.
        :return: None
        """
        cls.all_sessions.append(driver_wrapper)

    @classmethod
    def remove_session(cls, driver_wrapper: DriverWrapper) -> None:
        """
        Removes a :obj:`.DriverWrapper` object from the session pool.

        :param driver_wrapper: The :obj:`.DriverWrapper` instance to remove from the pool.
        :return: None
        """
        cls.all_sessions.remove(driver_wrapper)

    @classmethod
    def sessions_count(cls) -> int:
        """
        Get the count of initialized :obj:`.DriverWrapper` objects.

        :return: :obj:`int` - The number of initialized sessions.
        """
        return len(cls.all_sessions)

    @classmethod
    def first_session(cls) -> Union[DriverWrapper, None]:
        """
        Get the first :obj:`.DriverWrapper` object from the session pool.

        :return: The first :obj:`.DriverWrapper` object in the pool, or `None` if no session exists.
        :rtype: typing.Union[DriverWrapper, None]
        """
        return cls.all_sessions[0] if cls.all_sessions else None

    @classmethod
    def is_connected(cls) -> bool:
        """
        Check the connection status of any :obj:`.DriverWrapper` object in the pool.

        :return: :obj:`bool` - :obj:`True` if at least one :obj:`.DriverWrapper` object is available,
          otherwise :obj:`False`.
        """
        return any(cls.all_sessions)


class DriverWrapper(InternalMixin, Logging, DriverWrapperABC):
    """
    A wrapper class for managing web and mobile driver instances,
    supporting Selenium, Appium, and Playwright.

    This class serves as a crossroad for interacting with different driver types,
    allowing for flexible management of web and mobile sessions.

    It also provides platform-specific flags and information to assist with automation tasks.
    """

    driver: Union[SeleniumDriver, AppiumDriver, PlaywrightDriver]
    context: PlaywrightContext
    browser: PlaywrightBrowser

    _object: str = 'driver_wrapper'
    _base_cls: Type[PlayDriver, MobileDriver, WebDriver] = None
    session: DriverWrapperSessions = DriverWrapperSessions
    anchor: Union[Element, None] = None

    is_desktop: bool = False
    is_selenium: bool = False
    is_playwright: bool = False
    is_mobile_resolution: bool = False

    is_appium: bool = False
    is_mobile: bool = False
    is_tablet: bool = False

    is_ios: bool = False
    is_ios_tablet: bool = False
    is_ios_mobile: bool = False

    is_android: bool = False
    is_android_tablet: bool = False
    is_android_mobile: bool = False

    is_simulator: bool = False
    is_real_device: bool = False

    browser_name: Union[str, None] = None

    def __new__(cls, *args, **kwargs):
        if cls.session.sessions_count() == 0:
            cls = super().__new__(cls)
        else:
            cls = super().__new__(type(f'ShadowDriverWrapper', (cls, ), get_attributes_from_object(cls)))  # noqa

        for name, _ in get_child_elements_with_names(cls, bool).items():
            setattr(cls, name, False)

        return cls

    def __repr__(self):
        cls = self.__class__

        label = 'desktop'
        if cls.is_android:
            label = 'android'
        elif cls.is_ios:
            label = 'ios'

        return f'{cls.__name__}({self.label}={self.driver}) at {hex(id(self))}, platform={label}'

    def __init__(self, driver: Driver):
        """
        Initializes the DriverWrapper instance based on the provided driver source.

        This constructor sets up the driver wrapper, which can support
        Appium, Selenium, or Playwright drivers.
        It also manages session tracking and platform-specific configurations,
        such as mobile resolution and platform type.

        :param driver: :obj:`.Driver` object that holds appium / selenium / playwright driver to initialize
        """
        self.__driver_container = driver
        self.session.add_session(self)
        self.label = f'{self.session.all_sessions.index(self) + 1}_driver'
        self.__init_base_class__()
        if driver.is_mobile_resolution:
            self.is_mobile_resolution = True
            self.is_desktop = False
            self.is_mobile = True

    def quit(self, silent: bool = False, trace_path: str = 'trace.zip'):
        """
        Quit the driver instance.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool

        **Selenium/Appium:**

        :param trace_path: Compatibility argument for Playwright.
        :type trace_path: str

        **Playwright:**

        :param trace_path: Path to the trace file.
        :type trace_path: str

        :return: :obj:`None`
        """
        if not silent:
            self.log('Quit driver instance')

        self._base_cls.quit(self, trace_path)
        self.session.remove_session(self)

    def save_screenshot(
            self,
            file_name: str,
            screenshot_base: Union[Image, bytes] = None,
            convert_type: str = None
    ) -> Image:
        """
        Takes a full screenshot of the driver and saves it to the specified path/filename.

        :param file_name: Path or filename for the screenshot.
        :type file_name: str
        :param screenshot_base: Screenshot binary or image to use (optional).
        :type screenshot_base: :obj:`bytes`, :class:`PIL.Image.Image`
        :param convert_type: Image conversion type before saving (optional).
        :type convert_type: str
        :return: :class:`PIL.Image.Image`
        """
        self.log(f'Save driver screenshot')

        image_object = screenshot_base
        if isinstance(screenshot_base, bytes) or screenshot_base is None:
            image_object = self.screenshot_image(screenshot_base)

        if convert_type:
            image_object = image_object.convert(convert_type)

        image_object.save(file_name)

        return image_object

    def get_scroll_position(self) -> int:
        """
        Returns the current vertical scroll position of the page.

        :return: :class:`int` - Current vertical scroll offset in pixels.
        """
        return self.execute_script('return window.pageYOffset')

    def assert_screenshot(
            self,
            filename: str = '',
            test_name: str = '',
            name_suffix: str = '',
            threshold: Union[int, float] = None,
            delay: Union[int, float] = None,
            remove: Union[Element, List[Element]] = None,
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
        :type threshold: typing.Optional[int or float]
        :param delay: The delay in seconds before taking the screenshot.
          If :obj:`None` - takes default delay.
        :type delay: typing.Optional[int or float]
        :param remove: :class:`Element` to remove from the screenshot.
          Can be a single element or a list of elements.
        :type remove: typing.Optional[Element or typing.List[Element]]
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

        hide_before_screenshot(hide, is_optional=False, dw=self)
        self.wait(delay)
        hide_before_screenshot(VisualComparison.always_hide, is_optional=True, dw=self)

        VisualComparison(self).assert_screenshot(
            filename=filename, test_name=test_name, name_suffix=name_suffix, threshold=threshold,
            remove=remove, fill_background=False, cut_box=cut_box
        )

        reveal_after_screenshot(VisualComparison.always_hide, dw=self)

    def soft_assert_screenshot(
            self,
            filename: str = '',
            test_name: str = '',
            name_suffix: str = '',
            threshold: Union[int, float] = None,
            delay: Union[int, float] = None,
            remove: Union[Element, List[Element]] = None,
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
        :type threshold: typing.Optional[int or float]
        :param delay: The delay in seconds before taking the screenshot.
          If :obj:`None` - takes default delay.
        :type delay: typing.Optional[int or float]
        :param remove: :class:`Element` to remove from the screenshot.
        :type remove: typing.Optional[Element or typing.List[Element]]
        :param cut_box: A :class:`.Box` specifying a region to cut from the screenshot.
            If :obj:`None`, no region is cut.
        :type cut_box: typing.Optional[Box]
        :param hide: :class:`Element` to hide in the screenshot.
          Can be a single element or a list of elements.
        :return: :class:`typing.Tuple` (:class:`bool`, :class:`str`) - result state and result message
        """
        try:
            self.assert_screenshot(filename, test_name, name_suffix, threshold, delay, remove, cut_box, hide)
        except AssertionError as exc:
            exc = str(exc)
            self.log(exc, level=LogLevel.ERROR)
            return False, exc

        return True, f'No visual mismatch found for entire screen'

    def __init_base_class__(self) -> None:
        """
        Get driver wrapper class in according to given driver source, and set him as base class

        :return: None
        """
        source_driver = self.__driver_container.driver

        if isinstance(source_driver, PlaywrightDriver):
            self.is_playwright = True
            self._base_cls = PlayDriver
        elif isinstance(source_driver, AppiumDriver):
            self.is_appium = True
            self._base_cls = MobileDriver
        elif isinstance(source_driver, SeleniumDriver):
            self.is_selenium = True
            self._base_cls = WebDriver
        else:
            raise DriverWrapperException(f'Cant specify {self.__class__.__name__}')

        self._set_static(self._base_cls)
        self._base_cls.__init__(self, driver_container=self.__driver_container)

        for name, value in self.__dict__.items():
            setattr(self.__class__, name, value)
