from dataclasses import dataclass
from typing import Union

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

    driver: Union[AppiumDriver, SeleniumWebDriver, PlaywrightDriver]
    context: Union[PlaywrightContext, None] = None
    instance: Union[PlaywrightBrowser, None] = None
    is_mobile_resolution: bool = False
