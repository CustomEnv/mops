from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver

from dyatel.dyatel_sel.core.core_driver import CoreDriver


class WebDriver(CoreDriver):

    def __init__(self, driver: SeleniumWebDriver):
        """
        Initializing of desktop web driver with selenium

        :param driver: selenium driver to initialize
        """
        super().__init__(driver=driver)

    def set_window_size(self, width: int, height: int) -> CoreDriver:
        """
        Sets the width and height of the current window

        :param width: the width in pixels to set the window to
        :param height: the height in pixels to set the window to
        :return: self
        """
        self.driver.set_window_size(width, height)
        return self
