from __future__ import annotations

from abc import ABC
from functools import cached_property
from typing import List, Union, Any, Tuple, TYPE_CHECKING

from playwright.sync_api import Page as PlaywrightPage

from mops.mixins.objects.box import Box
from selenium.webdriver.common.alert import Alert
from PIL import Image

from mops.mixins.objects.size import Size
from mops.utils.internal_utils import WAIT_EL, WAIT_UNIT

if TYPE_CHECKING:
    from mops.base.driver_wrapper import DriverWrapper, DriverWrapperSessions
    from mops.base.element import Element


class DriverWrapperABC(ABC):
    session: Union[DriverWrapperSessions, None] = None
    label: Union[str, None] = None
    original_tab: Union[str, PlaywrightPage, None] = None

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

    @cached_property
    def is_safari(self) -> bool:
        """
        Returns :obj:`True` if the current driver is Safari, otherwise :obj:`False`.

        :return: :obj:`bool`- :obj:`True` if the current driver is Safari, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    @cached_property
    def is_chrome(self) -> bool:
        """
        Returns :obj:`True` if the current driver is Chrome, otherwise :obj:`False`.

        :return: :obj:`bool`- :obj:`True` if the current driver is Chrome, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    @cached_property
    def is_firefox(self) -> bool:
        """
        Returns :obj:`True` if the current driver is Firefox, otherwise :obj:`False`.

        :return: :obj:`bool`- :obj:`True` if the current driver is Firefox, otherwise :obj:`False`.
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def wait(self, timeout: Union[int, float] = WAIT_UNIT, reason: str = '') -> DriverWrapper:
        """
        Pauses the execution for a specified amount of time.

        :param timeout: The time to sleep in seconds (can be an integer or float).
        :type timeout: typing.Union[int, float]

        :param reason: The waiting reason.
        :type reason: str

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def get(self, url: str, silent: bool = False) -> DriverWrapper:
        """
        Navigate to the given URL.

        :param url: The URL to navigate to.
        :type url: str
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def is_driver_opened(self) -> bool:
        """
        Check if the driver is open.

        :return: :obj:`bool` - :obj:`True` if the driver is open, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    def is_driver_closed(self) -> bool:
        """
        Check if the driver is closed.

        :return: :obj:`bool` - :obj:`True` if the driver is closed, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    @property
    def current_url(self) -> str:
        """
        Retrieve the current page URL.

        :return: :obj:`str` - The URL of the current page.
        """
        raise NotImplementedError()

    def refresh(self) -> DriverWrapper:
        """
        Reload the current page.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def go_forward(self) -> DriverWrapper:
        """
        Navigate forward in the browser.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def go_back(self) -> DriverWrapper:
        """
        Navigate backward in the browser.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def set_cookie(self, cookies: List[dict]) -> DriverWrapper:
        """
        Add a list of cookie dictionaries to the current session.

        Note: The domain should be in the format ".google.com" for a URL like "https://google.com/some/url/".

        :param cookies: A list of dictionaries, each containing cookie data.
        :type cookies: typing.List[dict]
        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def clear_cookies(self) -> DriverWrapper:
        """
        Delete all cookies in the current session.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def delete_cookie(self, name: str) -> DriverWrapper:
        """
        Delete a cookie by name.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def get_cookies(self) -> List[dict]:
        """
        Retrieve a list of cookie dictionaries corresponding to the cookies visible in the current session.

        :return: A list of dictionaries, each containing cookie data.
        :rtype: typing.List[typing.Dict]
        """
        raise NotImplementedError()

    def switch_to_frame(self, frame: Element) -> DriverWrapper:
        """
        Switch to a specified frame.

        :param frame: The frame element to switch to.
        :type frame: Element
        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def switch_to_default_content(self) -> DriverWrapper:
        """
        Switch back to the default content from a frame.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def execute_script(self, script: str, *args: Any) -> Any:
        """
        Synchronously executes JavaScript in the current window or frame.
        Compatible with Selenium's `execute_script` method.

        :param script: The JavaScript code to execute.
        :type script: str
        :param args: Any arguments to pass to the JavaScript.
        :type args: :obj:`typing.Any`
        :return: :obj:`typing.Any` - The result of the JavaScript execution.
        """
        raise NotImplementedError()

    def evaluate(self, expression: str, arg: Any = None) -> Any:
        """
        Playwright only: Synchronously executes JavaScript in the current window or frame.

        :param expression: The JavaScript code to execute.
        :type expression: str
        :param arg: Any arguments to pass to the JavaScript.
        :type arg: list
        :return: :obj:`typing.Any` - The result of the JavaScript execution.
        """
        raise NotImplementedError()

    def set_page_load_timeout(self, timeout: int = 30) -> DriverWrapper:
        """
        Set the maximum time to wait for a page load to complete before throwing an error.

        :param timeout: The timeout duration to set, in seconds.
        :type timeout: int
        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def set_window_size(self, size: Size) -> DriverWrapper:
        """
        Set the inner window size (viewport) of the current browser context.

        :param size: The desired inner window size as a :class:`.Size` object.
        :return: The current instance of :obj:`.DriverWrapper`.
        """
        raise NotImplementedError()

    def get_inner_window_size(self) -> Size:
        """
        Retrieve the inner window size (viewport) of the current browser context.

        :return: The size of the inner window as a :class:`.Size` object.
        """
        raise NotImplementedError()

    def get_window_size(self) -> Size:
        """
        Retrieve the outer window size of the current browser context.

        .. note::
            Playwright behaves differently in headless mode, where the reported window
             size may not reflect the actual dimensions.
            In contrast, Appium does not support retrieving the window size in the
             same way as traditional web browsers.

        :return: The size of the outer window as a :class:`.Size` object.
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def get_scroll_position(self) -> int:
        """
        Returns the current vertical scroll position of the page.

        :return: :class:`int` - Current vertical scroll offset in pixels.
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()

    def screenshot_image(self, screenshot_base: bytes = None) -> Image:
        """
        Returns a :class:`PIL.Image.Image` object representing the screenshot of the web page.
        Appium iOS: Removes native controls from image manually

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

    def get_all_tabs(self) -> List[str]:
        """
        Selenium/Playwright only: Retrieve all opened tabs.

        :return: A list of :class:`str`, each representing an open tab.
        :rtype: typing.List[str]
        """
        raise NotImplementedError()

    def create_new_tab(self) -> DriverWrapper:
        """
        Selenium/Playwright only: Create a new tab and switch to it.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper, now switched to the new tab.
        """
        raise NotImplementedError()

    def switch_to_original_tab(self) -> DriverWrapper:
        """
        Selenium/Playwright only: Switch back to the original tab.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper, now switched to the original tab.
        """
        raise NotImplementedError()

    def switch_to_tab(self, tab: int = -1) -> DriverWrapper:
        """
        Selenium/Playwright only: Switch to a specific tab.

        :param tab: The index of the tab to switch to, starting from 1. Default is the latest tab.
        :type tab: int
        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper, now switched to the specified tab.
        """
        raise NotImplementedError()

    def close_unused_tabs(self) -> DriverWrapper:
        """
        Selenium/Playwright only: Close all tabs except the original.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper,
          with all tabs except the original closed.
        """
        raise NotImplementedError()

    def click_by_coordinates(self, x: int, y: int, silent: bool = False) -> DriverWrapper:
        """
        Click at the specified coordinates on the screen.

        :param x: The x-axis coordinate to click at.
        :type x: int
        :param y: The y-axis coordinate to click at.
        :type y: int
        :param silent: If :obj:`True`, suppresses the log message. Default is :obj:`False`.
        :type silent: bool
        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def is_app_installed(self) -> bool:
        """
        Appium only: Check if the app is running.

        :return: :obj:`bool` - :obj:`True` if the app is running, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    def is_app_deleted(self) -> bool:
        """
        Appium only: Check if the app is deleted.

        :return: :obj:`bool` - :obj:`True` if the app is deleted, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    def is_app_closed(self) -> bool:
        """
        Appium only: Check if the app is closed.

        :return: :obj:`bool` - :obj:`True` if the app is closed, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    def is_app_in_foreground(self) -> bool:
        """
        Appium only: Check if the app is in the foreground.

        :return: :obj:`bool` - :obj:`True` if the app is in the foreground, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    def is_app_in_background(self) -> bool:
        """
        Appium only: Check if the app is in the background.

        :return: :obj:`bool` - :obj:`True` if the app is in the background, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    def terminate_app(self, bundle_id: str) -> bool:
        """
        Appium only: Terminates the application if it is running.

        :param bundle_id: The application ID of the app to terminate.
        :type bundle_id: str
        :return: :obj:`bool` - :obj:`True` if the app has been successfully terminated, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    def switch_to_native(self) -> DriverWrapper:
        """
        Appium only: Switch to the native app context.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper, now in the native app context.
        """
        raise NotImplementedError()

    def switch_to_web(self) -> DriverWrapper:
        """
        Appium only: Switch to the web app context.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper, now in the web app context.
        """
        raise NotImplementedError()

    def get_web_view_context(self) -> Union[None, str]:
        """
        Appium only: Get the WEBVIEW context name.

        :return: :obj:`None` if no WEBVIEW context is found, otherwise the name of the WEBVIEW context.
        :rtype: typing.Union[None, str]
        """
        raise NotImplementedError()

    def get_current_context(self) -> str:
        """
        Appium only: Get the current context name.

        :return: :class:`str` - The name of the current context.
        """
        raise NotImplementedError()

    def is_native_context(self) -> bool:
        """
        Appium only: Check if the current context is native.

        :return: :obj:`bool` - :obj:`True` if the current context is native, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    def is_web_context(self) -> bool:
        """
        Appium only: Check if the current context is web.

        :return: :obj:`bool` - :obj:`True` if the current context is web, otherwise :obj:`False`.
        """
        raise NotImplementedError()

    def get_all_contexts(self) -> List[str]:
        """
        Appium only: Get all contexts within the current session.

        :return: A list of available context names.
        :rtype: typing.List[str]
        """
        raise NotImplementedError()

    def hide_keyboard(self, **kwargs) -> DriverWrapper:
        """
        Appium only: Hide the keyboard on a real device.

        :param kwargs: Additional arguments passed to the `Keyboard.hide_keyboard` method.
        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    @property
    def top_bar_height(self) -> int:
        """
        iOS only - Get the height of the top bar.

        :return: :obj:`int` - The height of the top bar in pixels.
        """
        raise NotImplementedError()

    @property
    def bottom_bar_height(self) -> int:
        """
        iOS only - Get the height of the bottom bar.

        :return: :obj:`int` - The height of the bottom bar in pixels.
        """
        raise NotImplementedError()

    def switch_to_alert(self, timeout: Union[int, float] = WAIT_EL) -> Alert:
        """
        Appium/Selenium only: Wait for an alert and switch to it.

        :param timeout: The time to wait for the alert to appear (in seconds).
        :type timeout: Union[int, float]
        :return: :obj:`selenium.webdriver.common.alert.Alert` - The alert object.
        """
        raise NotImplementedError()

    def accept_alert(self) -> DriverWrapper:
        """
        Appium/Selenium only: Wait for an alert, switch to it, and click accept.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()

    def dismiss_alert(self) -> DriverWrapper:
        """
        Appium/Selenium only: Wait for an alert, switch to it, and click dismiss.

        :return: :obj:`.DriverWrapper` - The current instance of the driver wrapper.
        """
        raise NotImplementedError()


