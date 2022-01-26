import os

import pytest
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver

from selenium_master.driver.web_driver import WebDriver
from data_for_testing.utils import set_logging_settings
from data_for_testing.pages.tabs_page import TabsPage
from data_for_testing.pages.sidebar_page import SidebarPage


set_logging_settings()


sidebar_page_path = f'file://{os.getcwd()}/data_for_testing/sidebar_page.html'
tabs_page_path = f'file://{os.getcwd()}/data_for_testing/tabs_page.html'


def pytest_addoption(parser):
    parser.addoption('--headless', action='store_true', help='Run in headless mode')


@pytest.fixture
def chrome_options(request):
    options = ChromeOptions()
    if request.config.getoption('headless'):
        options.headless = True
    return options


@pytest.fixture
def driver(chrome_options, request):
    web_driver = WebDriver(driver=ChromeWebDriver(options=chrome_options))
    web_driver.implicitly_wait(5)
    web_driver.set_window_size(1024, 900)
    web_driver.set_window_position(0, 0)
    all_pytest_markers = [marker.name for marker in request.node.own_markers]
    yield web_driver
    if 'no_teardown' not in all_pytest_markers:
        web_driver.quit()


@pytest.fixture
def sidebar_page(driver):
    driver.get(sidebar_page_path)
    return SidebarPage().wait_page_loaded()


@pytest.fixture
def tabs_page(driver):
    driver.get(tabs_page_path)
    return TabsPage().wait_page_loaded()
