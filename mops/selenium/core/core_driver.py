from __future__ import annotations

import time
from functools import cached_property
from typing import Union, List, Any, TYPE_CHECKING

from PIL import Image
from appium.webdriver.webdriver import WebDriver as AppiumDriver

from mops.js_scripts import get_inner_height_js, get_inner_width_js
from mops.mixins.objects.size import Size
from mops.shared_utils import _scaled_screenshot
from selenium.common.exceptions import WebDriverException as SeleniumWebDriverException, NoAlertPresentException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver

from mops.abstraction.driver_wrapper_abc import DriverWrapperABC
from mops.selenium.sel_utils import ActionChains
from mops.exceptions import DriverWrapperException, TimeoutException
from mops.utils.internal_utils import WAIT_EL, WAIT_UNIT
from mops.utils.logs import Logging

if TYPE_CHECKING:
    from mops.base.element import Element


class CoreDriver(Logging, DriverWrapperABC):

    driver: Union[AppiumDriver, SeleniumWebDriver]

    def __init__(self, driver: Union[AppiumDriver, SeleniumWebDriver]):
        """
        Initializing of core driver
        Contain same methods/data for both WebDriver and MobileDriver classes

        :param driver: appium or selenium driver to initialize
        """
        driver.implicitly_wait(0.001)  # reduce selenium wait

    @cached_property
    def is_safari(self) -> bool:
        """
        Returns :obj:`True` if the current driver is Safari, otherwise :obj:`False`.

        :return: :obj:`bool`- :obj:`True` if the current driver is Safari, otherwise :obj:`False`.
        """
        return self.browser_name.lower() == 'safari'

    @cached_property
    def is_chrome(self) -> bool:
        """
        Returns :obj:`True` if the current driver is Chrome, otherwise :obj:`False`.

        :return: :obj:`bool`- :obj:`True` if the current driver is Chrome, otherwise :obj:`False`.
        """
        return self.browser_name.lower() == 'chrome'

    @cached_property
    def is_firefox(self) -> bool:
        """
        Returns :obj:`True` if the current driver is Firefox, otherwise :obj:`False`.

        :return: :obj:`bool`- :obj:`True` if the current driver is Firefox, otherwise :obj:`False`.
        """
        return self.browser_name.lower() == 'firefox'

    def get_inner_window_size(self) -> Size:
        """
        Retrieve the inner window size (viewport) of the current browser context.

        :return: The size of the inner window as a :class:`.Size` object.
        """
        return Size(
            height=self.execute_script(get_inner_height_js),
            width=self.execute_script(get_inner_width_js)
        )

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
        return Size(**self.driver.get_window_size())

    def wait(self, timeout: Union[int, float] = WAIT_UNIT, reason: str = '') -> CoreDriver:
        """
        Pauses the execution for a specified amount of time.

        :param timeout: The time to sleep in seconds (can be an integer or float).
        :type timeout: typing.Union[int, float]

        :param reason: The waiting reason.
        :type reason: str

        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        if reason:
            self.log(reason)

        time.sleep(timeout)
        return self

    def get(self, url: str, silent: bool = False) -> CoreDriver:
        """
        Navigate to the given URL.

        :param url: The URL to navigate to.
        :type url: str
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        if not silent:
            self.log(f'Navigating to url {url}')

        try:
            self.driver.get(url)
        except SeleniumWebDriverException as exc:
            raise DriverWrapperException(f'Can\'t proceed to {url}. Original error: {exc.msg}')

        return self

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
        return _scaled_screenshot(screenshot_base, self.get_inner_window_size().width)

    @property
    def screenshot_base(self) -> bytes:
        """
        Returns the binary screenshot data of the element.

        :return: :class:`bytes` - screenshot binary
        """
        return self.driver.get_screenshot_as_png()

    def is_driver_opened(self) -> bool:
        """
        Check if the driver is open.

        :return: :obj:`bool` - :obj:`True` if the driver is open, otherwise :obj:`False`.
        """
        return True if self.driver else False

    def is_driver_closed(self) -> bool:
        """
        Check if the driver is closed.

        :return: :obj:`bool` - :obj:`True` if the driver is closed, otherwise :obj:`False`.
        """
        return False if self.driver else True

    @property
    def current_url(self) -> str:
        """
        Retrieve the current page URL.

        :return: :obj:`str` - The URL of the current page.
        """
        return self.driver.current_url

    def refresh(self) -> CoreDriver:
        """
        Reload the current page.

        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.log('Reload current page')
        self.driver.refresh()
        return self

    def go_forward(self) -> CoreDriver:
        """
        Navigate forward in the browser.

        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.log('Going forward')
        self.driver.forward()
        return self

    def go_back(self) -> CoreDriver:
        """
        Navigate backward in the browser.

        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.log('Going back')
        self.driver.back()
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
        self.driver.quit()

    def set_cookie(self, cookies: List[dict]) -> CoreDriver:
        """
        Add a list of cookie dictionaries to the current session.

        Note: The domain should be in the format ".google.com" for a URL like "https://google.com/some/url/".

        :param cookies: A list of dictionaries, each containing cookie data.
        :type cookies: typing.List[dict]
        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        for cookie in cookies:

            if 'path' not in cookie:
                cookie.update({'path': '/'})

            self.driver.add_cookie(cookie)

        return self

    def clear_cookies(self) -> CoreDriver:
        """
        Delete all cookies in the current session.

        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.driver.delete_all_cookies()
        return self

    def delete_cookie(self, name: str) -> CoreDriver:
        """
        Delete a cookie by name.

        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.driver.delete_cookie(name)
        return self

    def get_cookies(self) -> List[dict]:
        """
        Retrieve a list of cookie dictionaries corresponding to the cookies visible in the current session.

        :return: A list of dictionaries, each containing cookie data.
        :rtype: typing.List[typing.Dict]
        """
        return self.driver.get_cookies()

    def switch_to_frame(self, frame: Element) -> CoreDriver:
        """
        Switch to a specified frame.

        :param frame: The frame element to switch to.
        :type frame: Element
        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.driver.switch_to.frame(frame.element)
        return self

    def switch_to_default_content(self) -> CoreDriver:
        """
        Switch back to the default content from a frame.

        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.driver.switch_to.default_content()
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
        args = [getattr(arg, 'element', arg) for arg in args]
        return self.driver.execute_script(script, *args)

    def set_page_load_timeout(self, timeout: int = 30) -> CoreDriver:
        """
        Set the maximum time to wait for a page load to complete before throwing an error.

        :param timeout: The timeout duration to set, in seconds.
        :type timeout: int
        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.driver.set_page_load_timeout(timeout)
        return self

    def switch_to_alert(self, timeout: Union[int, float] = WAIT_EL) -> Alert:
        """
        Appium/Selenium only: Wait for an alert and switch to it.

        :param timeout: The time to wait for the alert to appear (in seconds).
        :type timeout: Union[int, float]
        :return: :obj:`selenium.webdriver.common.alert.Alert` - The alert object.
        """
        alert = None
        end_time = time.time() + timeout

        while not alert and time.time() < end_time:
            try:
                alert = self.driver.switch_to.alert
            except NoAlertPresentException:
                alert = None

        if not alert:
            raise TimeoutException(f'Alert not found after {timeout} seconds')

        return alert

    def accept_alert(self) -> CoreDriver:
        """
        Appium/Selenium only: Wait for an alert, switch to it, and click accept.

        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.switch_to_alert().accept()
        self.switch_to_default_content()
        return self

    def dismiss_alert(self) -> CoreDriver:
        """
        Appium/Selenium only: Wait for an alert, switch to it, and click dismiss.

        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        self.switch_to_alert().dismiss()
        self.switch_to_default_content()
        return self

    def click_by_coordinates(self, x: int, y: int, silent: bool = False) -> CoreDriver:
        """
        Click at the specified coordinates on the screen.

        :param x: The x-axis coordinate to click at.
        :type x: int
        :param y: The y-axis coordinate to click at.
        :type y: int
        :param silent: If :obj:`True`, suppresses the log message. Default is :obj:`False`.
        :type silent: bool
        :return: :obj:`.CoreDriver` - The current instance of the driver wrapper.
        """
        if not silent:
            self.log(f'Click by given coordinates (x: {x}, y: {y})')

        ActionChains(self.driver).move_to_location(x, y).click().perform()
        return self
