from __future__ import annotations

from dataclasses import asdict
from functools import cached_property
from typing import List, Union, Any, TYPE_CHECKING

from playwright._impl._errors import Error as PlaywrightError  # noqa

from PIL import Image
from playwright.sync_api import Locator, Page, Browser, BrowserContext

from mops.abstraction.driver_wrapper_abc import DriverWrapperABC
from mops.mixins.objects.driver import Driver
from mops.mixins.objects.size import Size
from mops.shared_utils import get_image
from mops.utils.internal_utils import get_timeout_in_ms, WAIT_UNIT
from mops.utils.logs import Logging

if TYPE_CHECKING:
    from mops.base.element import Element


class PlayDriver(Logging, DriverWrapperABC):

    def __init__(self, driver_container: Driver):
        """
        Initializing of desktop web driver with playwright

        :param driver_container: Driver that contains playwright instance, context and driver objects
        """
        self.is_desktop = True

        self.instance: Browser = driver_container.instance
        self.context: BrowserContext = driver_container.context
        self.driver: Page = driver_container.driver

        self.original_tab = self.driver
        self.browser_name = self.instance.browser_type.name

        self._base_driver = self.driver

    @cached_property
    def is_safari(self) -> bool:
        """
        Returns :obj:`True` if the current driver is Safari, otherwise :obj:`False`.

        :return: :obj:`bool`- :obj:`True` if the current driver is Safari, otherwise :obj:`False`.
        """
        return self.browser_name.lower() == 'webkit'

    @cached_property
    def is_chrome(self) -> bool:
        """
        Returns :obj:`True` if the current driver is Chrome, otherwise :obj:`False`.

        :return: :obj:`bool`- :obj:`True` if the current driver is Chrome, otherwise :obj:`False`.
        """
        return self.browser_name.lower() == 'chromium'

    @cached_property
    def is_firefox(self) -> bool:
        """
        Returns :obj:`True` if the current driver is Firefox, otherwise :obj:`False`.

        :return: :obj:`bool`- :obj:`True` if the current driver is Firefox, otherwise :obj:`False`.
        """
        return self.browser_name.lower() == 'firefox'

    def wait(self, timeout: Union[int, float] = WAIT_UNIT, reason: str = '') -> PlayDriver:
        """
        Pauses the execution for a specified amount of time.

        :param timeout: The time to sleep in seconds (can be an integer or float).
        :type timeout: typing.Union[int, float]

        :param reason: The waiting reason.
        :type reason: str

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        if reason:
            self.log(reason)

        self.driver.wait_for_timeout(get_timeout_in_ms(timeout))
        return self

    def get(self, url: str, silent: bool = False) -> PlayDriver:
        """
        Navigate to the given URL.

        :param url: The URL to navigate to.
        :type url: str
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        if not silent:
            self.log(f'Navigating to url {url}')

        self.driver.goto(url)
        return self

    def is_driver_opened(self) -> bool:
        """
        Check if the driver is open.

        :return: :obj:`bool` - :obj:`True` if the driver is open, otherwise :obj:`False`.
        """
        return self.instance.is_connected()

    def is_driver_closed(self) -> bool:
        """
        Check if the driver is closed.

        :return: :obj:`bool` - :obj:`True` if the driver is closed, otherwise :obj:`False`.
        """
        return not self.instance.is_connected()

    @property
    def current_url(self) -> str:
        """
        Retrieve the current page URL.

        :return: :obj:`str` - The URL of the current page.
        """
        return self.driver.url

    def refresh(self) -> PlayDriver:
        """
        Reload the current page.

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        self.log('Reload current page')
        self.driver.reload(wait_until='load')
        return self

    def go_forward(self) -> PlayDriver:
        """
        Navigate forward in the browser.

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        self.log('Going forward')
        self.driver.go_forward()
        return self

    def go_back(self) -> PlayDriver:
        """
        Navigate backward in the browser.

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        self.log('Going back')
        self.driver.go_back()
        return self

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
        if trace_path:
            try:
                self.context.tracing.stop(path=trace_path)
            except PlaywrightError:
                pass

        self._base_driver.close()
        self.context.close()

    def set_cookie(self, cookies: List[dict]) -> PlayDriver:
        """
        Add a list of cookie dictionaries to the current session.

        Note: The domain should be in the format ".google.com" for a URL like "https://google.com/some/url/".

        :param cookies: A list of dictionaries, each containing cookie data.
        :type cookies: typing.List[dict]
        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        for cookie in cookies:

            if 'path' not in cookie:
                cookie.update({'path': '/'})

            if 'domain' not in cookie:
                cookie.update({'domain': f'.{self.current_url.split("://")[1].split("/")[0]}'})

        self.context.add_cookies(cookies)
        return self

    def clear_cookies(self) -> PlayDriver:
        """
        Delete all cookies in the current session.

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        self.context.clear_cookies()
        return self

    def delete_cookie(self, name: str) -> PlayDriver:
        """
        Delete a cookie by name.

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        self.context.clear_cookies(name=name)
        return self

    def get_cookies(self) -> List[dict]:
        """
        Retrieve a list of cookie dictionaries corresponding to the cookies visible in the current session.

        :return: A list of dictionaries, each containing cookie data.
        :rtype: typing.List[typing.Dict]
        """
        return self.context.cookies()

    def switch_to_frame(self, frame: Element) -> PlayDriver:
        """
        Switch to a specified frame.

        :param frame: The frame element to switch to.
        :type frame: Element
        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        self.driver = frame.element.content_frame
        return self

    def switch_to_default_content(self) -> PlayDriver:
        """
        Switch back to the default content from a frame.

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        self.driver = self._base_driver
        return self

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
        script = script.replace('return ', '')

        if 'arguments[0]' in script:
            args = [getattr(arg, 'element', arg) for arg in args]
            script = f'arguments => {{{script}}}'

        for index, arg in enumerate(args):
            if isinstance(arg, Locator):
                args[index] = arg.first.element_handle()

        return self.driver.evaluate(script, args)

    def evaluate(self, expression: str, arg: Any = None) -> Any:
        """
        Playwright only: Synchronously executes JavaScript in the current window or frame.

        :param expression: The JavaScript code to execute.
        :type expression: str
        :param arg: Any arguments to pass to the JavaScript.
        :type arg: list
        :return: :obj:`typing.Any` - The result of the JavaScript execution.
        """
        return self.driver.evaluate(expression=expression, arg=arg)

    def set_page_load_timeout(self, timeout: int = 30) -> PlayDriver:
        """
        Set the maximum time to wait for a page load to complete before throwing an error.

        :param timeout: The timeout duration to set, in seconds.
        :type timeout: int
        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        self.driver.set_default_navigation_timeout(get_timeout_in_ms(timeout))
        return self

    def set_window_size(self, size: Size) -> PlayDriver:
        """
        Set the inner window size (viewport) of the current browser context.

        :param size: The desired inner window size as a :class:`.Size` object.
        :return: The current instance of :obj:`.PlayDriver`.
        """
        self.driver.set_viewport_size(asdict(size))
        return self

    def get_inner_window_size(self) -> Size:
        """
        Retrieve the inner window size (viewport) of the current browser context.

        :return: The size of the inner window as a :class:`.Size` object.
        """
        return Size(**self.driver.viewport_size)

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
        width = self.execute_script('return window.outerWidth')
        height = self.execute_script('return window.outerHeight')
        return Size(width=width, height=height)

    def screenshot_image(self, screenshot_base: bytes = None) -> Image:
        """
        Returns a :class:`PIL.Image.Image` object representing the screenshot of the web page.
        Appium iOS: Removes native controls from image manually

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
        return self.driver.screenshot()

    def get_all_tabs(self) -> List[Page]:
        """
        Selenium/Playwright only: Retrieve all opened tabs.

        :return: A list of :class:`str`, each representing an open tab.
        :rtype: typing.List[str]
        """
        return self.context.pages

    def create_new_tab(self) -> PlayDriver:
        """
        Selenium/Playwright only: Create a new tab and switch to it.

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper, now switched to the new tab.
        """
        with self.context.expect_page() as new_page:
            self.execute_script("window.open(arguments[0], '_blank').focus();", self.current_url)

        self.driver = new_page.value
        return self

    def switch_to_original_tab(self) -> PlayDriver:
        """
        Selenium/Playwright only: Switch back to the original tab.

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper, now switched to the original tab.
        """
        self.driver = self.original_tab
        self.driver.bring_to_front()
        return self

    def switch_to_tab(self, tab: int = -1) -> PlayDriver:
        """
        Selenium/Playwright only: Switch to a specific tab.

        :param tab: The index of the tab to switch to, starting from 1. Default is the latest tab.
        :type tab: int
        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper, now switched to the specified tab.
        """
        if tab == -1:
            tab = self.get_all_tabs()[tab]
        else:
            tab = self.get_all_tabs()[tab - 1]

        self.driver = tab
        self.driver.bring_to_front()
        return self

    def close_unused_tabs(self) -> PlayDriver:
        """
        Selenium/Playwright only: Close all tabs except the original.

        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper,
          with all tabs except the original closed.
        """
        tabs = self.get_all_tabs()
        tabs.remove(self.original_tab)

        for tab in tabs:
            tab.close()

        return self.switch_to_original_tab()

    def click_by_coordinates(self, x: int, y: int, silent: bool = False) -> PlayDriver:
        """
        Click at the specified coordinates on the screen.

        :param x: The x-axis coordinate to click at.
        :type x: int
        :param y: The y-axis coordinate to click at.
        :type y: int
        :param silent: If :obj:`True`, suppresses the log message. Default is :obj:`False`.
        :type silent: bool
        :return: :obj:`.PlayDriver` - The current instance of the driver wrapper.
        """
        if not silent:
            self.log(f'Click by given coordinates (x: {x}, y: {y})')

        self.driver.mouse.click(x=x, y=y)
        return self
