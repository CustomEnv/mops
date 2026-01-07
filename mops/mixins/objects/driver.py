from dataclasses import dataclass

from appium.webdriver.webdriver import WebDriver as AppiumDriver
from playwright.sync_api import (
    Browser as PlaywrightBrowser,
    BrowserContext as PlaywrightContext,
    Page as PlaywrightDriver,
)
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver


@dataclass
class Driver:
    """Represents a web or mobile driver, supporting Appium, Selenium, and Playwright."""

    driver: AppiumDriver | SeleniumWebDriver | PlaywrightDriver
    context: PlaywrightContext | None = None
    instance: PlaywrightBrowser | None = None
    is_mobile_resolution: bool = False
