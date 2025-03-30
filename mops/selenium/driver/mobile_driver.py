from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from appium.webdriver.applicationstate import ApplicationState

from mops.mixins.native_context import NativeContext, NativeSafari
from mops.selenium.core.core_driver import CoreDriver

if TYPE_CHECKING:
    from appium.webdriver.webdriver import WebDriver as AppiumDriver


class MobileDriver(CoreDriver):

    bundle_id: Optional[str]

    def __init__(self, driver_container: Driver, *args, **kwargs):  # noqa
        """
        Initializing of mobile driver with appium.

        :param driver_container: Driver that contains appium driver object
        """
        self.driver: AppiumDriver = driver_container.driver
        self.caps = self.driver.capabilities
        self.browser_name = self.caps.get('browserName', None)
        self.is_web = bool(self.browser_name) or False
        self.is_app = self.caps.get('app', False)

        _set_static(self)

        self.native_context_name = 'NATIVE_APP'
        self.web_context_name = self.get_web_view_context() if self.is_ios else 'CHROMIUM'
        self.__is_native_context = None
        self.__is_web_context = None

        self._top_bar_height = None
        self._bottom_bar_height = None

        self.original_tab = None
        self.page_box = None

        self.native_safari = NativeSafari(self)

        CoreDriver.__init__(self, driver=self.driver)

    def is_app_installed(self) -> bool:
        """
        Appium only: Check if the app is running.

        :return: :obj:`bool` - :obj:`True` if the app is running, otherwise :obj:`False`.
        """
        return self.driver.query_app_state(self.bundle_id) == ApplicationState.RUNNING_IN_FOREGROUND

    def is_app_deleted(self) -> bool:
        """
        Appium only: Check if the app is deleted.

        :return: :obj:`bool` - :obj:`True` if the app is deleted, otherwise :obj:`False`.
        """
        if self.is_ios:  # query_app_state return value equal 1(NOT_RUNNING), that not accurate
            return not self.is_app_installed()

        return self.driver.query_app_state(self.bundle_id) == ApplicationState.NOT_INSTALLED

    def is_app_closed(self) -> bool:
        """
        Appium only: Check if the app is closed.

        :return: :obj:`bool` - :obj:`True` if the app is closed, otherwise :obj:`False`.
        """
        return self.driver.query_app_state(self.bundle_id) == ApplicationState.NOT_RUNNING

    def is_app_in_foreground(self) -> bool:
        """
        Appium only: Check if the app is in the foreground.

        :return: :obj:`bool` - :obj:`True` if the app is in the foreground, otherwise :obj:`False`.
        """
        return self.driver.query_app_state(self.bundle_id) == ApplicationState.RUNNING_IN_FOREGROUND

    def is_app_in_background(self) -> bool:
        """
        Appium only: Check if the app is in the background.

        :return: :obj:`bool` - :obj:`True` if the app is in the background, otherwise :obj:`False`.
        """
        background_state = ApplicationState.RUNNING_IN_BACKGROUND

        if self.is_ios:  # iOS simulator are suspended the background app
            background_state = ApplicationState.RUNNING_IN_BACKGROUND_SUSPENDED

        return self.driver.query_app_state(self.bundle_id) == background_state

    def terminate_app(self, bundle_id: str) -> bool:
        """
        Appium only: Terminates the application if it is running.

        :param bundle_id: The application ID of the app to terminate.
        :type bundle_id: str
        :return: :obj:`bool` - :obj:`True` if the app has been successfully terminated, otherwise :obj:`False`.
        """
        return self.driver.terminate_app(bundle_id)

    def switch_to_native(self) -> MobileDriver:
        """
        Appium only: Switch to the native app context.

        :return: :obj:`.MobileDriver` - The current instance of the driver wrapper, now in the native app context.
        """
        self.driver.switch_to.context(self.native_context_name)
        self.__is_native_context = True
        self.__is_web_context = False
        return self

    def switch_to_web(self) -> MobileDriver:
        """
        Appium only: Switch to the web app context.

        :return: :obj:`.MobileDriver` - The current instance of the driver wrapper, now in the web app context.
        """
        self.driver.switch_to.context(self.web_context_name)
        self.__is_native_context = False
        self.__is_web_context = True
        return self

    def get_web_view_context(self) -> Union[None, str]:
        """
        Appium only: Get the WEBVIEW context name.

        :return: :obj:`None` if no WEBVIEW context is found, otherwise the name of the WEBVIEW context.
        :rtype: typing.Union[None, str]
        """
        for context in self.get_all_contexts():
            if 'WEBVIEW' in context:
                return context
        return None

    def get_current_context(self) -> str:
        """
        Appium only: Get the current context name.

        :return: :class:`str` - The name of the current context.
        """
        return self.driver.context

    @property
    def is_native_context(self) -> bool:
        """
        Appium only: Check if the current context is native.

        :return: :obj:`bool` - :obj:`True` if the current context is native, otherwise :obj:`False`.
        """
        if self.__is_native_context is None:
            self.__is_native_context = self.get_current_context() == self.native_context_name

        return self.__is_native_context

    @property
    def is_web_context(self) -> bool:
        """
        Appium only: Check if the current context is web.

        :return: :obj:`bool` - :obj:`True` if the current context is web, otherwise :obj:`False`.
        """
        if self.__is_web_context is None:
            self.__is_web_context = self.get_current_context() == self.web_context_name

        return self.__is_web_context

    @property
    def top_bar_height(self) -> int:
        """
        IOS only - Get the height of the top bar.

        :return: :obj:`int` - The height of the top bar in pixels.
        """
        if self._top_bar_height is None:
            with NativeContext(self):
                self._top_bar_height = self.native_safari.top_bar.size.height

        return self._top_bar_height

    @property
    def bottom_bar_height(self) -> int:
        """
        IOS only - Get the height of the bottom bar.

        :return: :obj:`int` - The height of the bottom bar in pixels.
        """
        if self.is_tablet:
            return 0

        if self._bottom_bar_height is None:
            with NativeContext(self):
                self._bottom_bar_height = self.native_safari.get_bottom_bar_height()

        return self._bottom_bar_height

    def get_all_contexts(self) -> List[str]:
        """
        Appium only: Get all contexts within the current session.

        :return: A list of available context names.
        :rtype: typing.List[str]
        """
        return self.driver.contexts

    def screenshot_image(self, screenshot_base: Optional[bytes] = None):
        """
        Returns a :class:`PIL.Image.Image` object representing the screenshot of the web page.
        Appium iOS: Removes native controls from image manually.

        :param screenshot_base: Screenshot binary data (optional).
          If :obj:`None` is provided then takes a new screenshot
        :type screenshot_base: bytes
        :return: :class:`PIL.Image.Image`
        """
        image = CoreDriver.screenshot_image(self, screenshot_base)

        if self.is_ios and not screenshot_base:
            if not self.page_box:
                width, height = image.size
                self.page_box = 0, self.top_bar_height, width, height - self.bottom_bar_height

            image = image.crop(self.page_box)

        return image

    def hide_keyboard(self, **kwargs) -> MobileDriver:
        """
        Appium only: Hide the keyboard on a real device.

        :param kwargs: Additional arguments passed to the `Keyboard.hide_keyboard` method.
        :return: :obj:`.MobileDriver` - The current instance of the driver wrapper.
        """
        if self.is_real_device:
            self.driver.hide_keyboard(**kwargs)

        elif self.is_ios and self.is_simulator:
            with NativeContext(self):
                if self.native_safari.keyboard_done_button.is_displayed():
                    self.native_safari.keyboard_done_button.click()

        return self

    def click_by_coordinates(self, x: int, y: int, silent: bool = False) -> MobileDriver:
        """
        Click at the specified coordinates on the screen.

        :param x: The x-axis coordinate to click at.
        :type x: int
        :param y: The y-axis coordinate to click at.
        :type y: int
        :param silent: If :obj:`True`, suppresses the log message. Default is :obj:`False`.
        :type silent: bool
        :return: :obj:`.MobileDriver` - The current instance of the driver wrapper.
        """
        if not silent:
            self.log(f'Tap by given coordinates (x: {x}, y: {y})')

        if self.is_ios:
            self.driver.tap(positions=[(x, y)])
        elif self.is_android:
            CoreDriver.click_by_coordinates(self, x=x, y=y, silent=True)

        return self


def _set_static(obj) -> None:
    """
    Set static attributes for Appium driver wrapper.

    :return: None
    """
    obj.is_tablet = obj.caps.get('is_tablet', False)
    obj.is_mobile = not obj.is_tablet

    obj.is_ios = obj.caps.get('platformName').lower() == 'ios'
    obj.is_ios_tablet = obj.is_ios and obj.is_tablet
    obj.is_ios_mobile = obj.is_ios and obj.is_mobile

    obj.is_android = obj.caps.get('platformName').lower() == 'android'
    obj.is_android_tablet = obj.is_android and obj.is_tablet
    obj.is_android_mobile = obj.is_android and obj.is_mobile

    obj.is_simulator = obj.caps.get('useSimulator', False)
    obj.is_real_device = not obj.is_simulator

    if obj.is_app:
        if obj.is_ios:
            obj.bundle_id = obj.caps.get('bundleId', 'undefined: bundleId')
        elif obj.is_android:
            obj.bundle_id = obj.caps.get('appPackage', 'undefined: appPackage')
        else:
            msg = 'Make sure that correct "platformName" capability specified'
            raise Exception(msg)
