import pytest
from mops.mixins.objects.driver import Driver
from mock.mock import MagicMock

from playwright.sync_api import Browser, Page as PlaywrightSourcePage
from appium.webdriver.webdriver import WebDriver as AppiumDriver
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumDriver

from mops.base.driver_wrapper import DriverWrapper, DriverWrapperSessions
from mops.playwright.play_driver import PlayDriver
from mops.selenium.core.core_driver import CoreDriver


class MockedDriverWrapper(DriverWrapper):

    def dummy_element(self):
        from mops.base.element import Element
        return Element('dummy element', driver_wrapper=self)


@pytest.fixture
def mocked_shared_mobile_driver():
    appium_driver = AppiumDriver
    appium_driver.__init__ = lambda *args, **kwargs: None
    appium_driver.session_id = None
    appium_driver.command_executor = MagicMock()
    appium_driver.error_handler = MagicMock()
    return appium_driver


@pytest.fixture
def mocked_ios_driver(mocked_shared_mobile_driver):
    mocked_shared_mobile_driver.capabilities = MagicMock(
        return_value={
            'platformName': 'ios',
            'browserName': 'safari',
            'automationName': 'safari'
        }
    )()
    driver_wrapper = MockedDriverWrapper(Driver(driver=mocked_shared_mobile_driver()))
    yield driver_wrapper
    DriverWrapperSessions.all_sessions = []


@pytest.fixture
def mocked_android_driver(mocked_shared_mobile_driver):
    mocked_shared_mobile_driver.capabilities = MagicMock(
        return_value={
            'platformName': 'Android',
            'browserName': 'chrome',
            'automationName': 'UiAutomator2'
        }
    )()
    driver_wrapper = MockedDriverWrapper(Driver(driver=mocked_shared_mobile_driver()))
    yield driver_wrapper
    DriverWrapperSessions.all_sessions = []


@pytest.fixture
def mocked_ios_tablet_driver(mocked_shared_mobile_driver):
    mocked_shared_mobile_driver.capabilities = MagicMock(
        return_value={
            'platformName': 'ios',
            'browserName': 'safari',
            'automationName': 'safari',
            'is_tablet': True,
        }
    )()
    driver_wrapper = MockedDriverWrapper(Driver(driver=mocked_shared_mobile_driver()))
    yield driver_wrapper
    DriverWrapperSessions.all_sessions = []


@pytest.fixture
def mocked_android_tablet_driver(mocked_shared_mobile_driver):
    mocked_shared_mobile_driver.capabilities = MagicMock(
        return_value={
            'platformName': 'Android',
            'browserName': 'chrome',
            'automationName': 'UiAutomator2',
            'is_tablet': True,
        }
    )()
    driver_wrapper = MockedDriverWrapper(Driver(driver=mocked_shared_mobile_driver()))
    yield driver_wrapper
    DriverWrapperSessions.all_sessions = []


@pytest.fixture
def mocked_selenium_driver():
    selenium_driver = SeleniumDriver
    selenium_driver.__init__ = lambda *args, **kwargs: None
    selenium_driver.session_id = None
    selenium_driver.command_executor = MagicMock()
    selenium_driver.error_handler = MagicMock()

    selenium_driver.caps = {}
    driver_wrapper = MockedDriverWrapper(Driver(driver=selenium_driver()))
    yield driver_wrapper
    DriverWrapperSessions.all_sessions = []


@pytest.fixture
def mocked_selenium_mobile_driver():
    selenium_driver = SeleniumDriver
    selenium_driver.__init__ = lambda *args, **kwargs: None
    selenium_driver.session_id = None
    selenium_driver.command_executor = MagicMock()
    selenium_driver.error_handler = MagicMock()

    selenium_driver.caps = {}
    driver_wrapper = MockedDriverWrapper(Driver(driver=selenium_driver(), is_mobile_resolution=True))
    yield driver_wrapper
    DriverWrapperSessions.all_sessions = []


@pytest.fixture
def mocked_play_driver():
    driver_wrapper = MockedDriverWrapper(
        Driver(
            driver=PlaywrightSourcePage(MagicMock()),
            instance=Browser(MagicMock())
        )
    )
    driver_wrapper.is_desktop = True
    yield driver_wrapper
    DriverWrapperSessions.all_sessions = []


@pytest.fixture
def mocked_play_mobile_driver():
    driver_wrapper = MockedDriverWrapper(
        Driver(
            driver=PlaywrightSourcePage(MagicMock()),
            instance=Browser(MagicMock()),
            is_mobile_resolution=True,
        )
    )
    yield driver_wrapper
    DriverWrapperSessions.all_sessions = []


@pytest.fixture(autouse=True)
def base_teardown():
    yield
    DriverWrapper.is_multiplatform = False
    DriverWrapper.is_mobile = False
    DriverWrapper.is_desktop = False
    DriverWrapper.is_ios = False
    DriverWrapper.is_android = False
    DriverWrapper.is_selenium = False
    DriverWrapper.is_playwright = False
    PlayDriver.driver = None
    CoreDriver.driver = None
    DriverWrapperSessions.all_sessions = []

    if '_framework_attrs' in MockedDriverWrapper.__dict__:
        framework_attrs = MockedDriverWrapper.__dict__['_framework_attrs']
        for attr in list(MockedDriverWrapper.__dict__.keys()):
            if not attr.startswith('_') and attr not in framework_attrs:
                try:
                    delattr(MockedDriverWrapper, attr)
                except AttributeError:
                    pass
        del MockedDriverWrapper._framework_attrs
    if '_configured' in MockedDriverWrapper.__dict__:
        del MockedDriverWrapper._configured


mobile_drivers = [mocked_ios_driver.__name__, mocked_android_driver.__name__]
mobile_ids = ['appium ios', 'appium android']


desktop_drivers = [mocked_selenium_driver.__name__, mocked_play_driver.__name__]
desktop_ids = ['selenium', 'playwright']


all_drivers = mobile_drivers + desktop_drivers
all_ids = mobile_ids + desktop_ids


selenium_drivers = [mocked_selenium_driver.__name__] + mobile_drivers
selenium_ids = ['selenium'] + mobile_ids
