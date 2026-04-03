import pytest

from mock.mock import MagicMock, PropertyMock, patch

from playwright.sync_api import Page as PlaywrightSourcePage, Browser
from playwright._impl._errors import Error as PlaywrightError

from selenium.common.exceptions import WebDriverException as SeleniumWebDriverException
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumDriver

from mops.base.driver_wrapper import DriverWrapper, DriverWrapperSessions
from mops.mixins.objects.driver import Driver


@pytest.fixture(autouse=True)
def cleanup_sessions():
    yield
    DriverWrapperSessions.all_sessions = []


def _make_playwright_wrapper(is_cdp=False):
    mock_page = PlaywrightSourcePage(MagicMock())
    mock_context = MagicMock()
    mock_browser = Browser(MagicMock())

    wrapper = DriverWrapper(Driver(driver=mock_page, context=mock_context, instance=mock_browser))
    wrapper.is_cdp = is_cdp
    return wrapper, mock_page, mock_context


def _make_selenium_wrapper(is_cdp=False):
    selenium_driver = SeleniumDriver
    selenium_driver.__init__ = lambda *args, **kwargs: None
    selenium_driver.session_id = None
    selenium_driver.command_executor = MagicMock()
    selenium_driver.error_handler = MagicMock()
    selenium_driver.caps = {}

    instance = selenium_driver()
    wrapper = DriverWrapper(Driver(driver=instance))
    wrapper.is_cdp = is_cdp
    return wrapper, instance


class TestIsCdpFlag:

    def test_is_cdp_defaults_to_false_playwright(self):
        wrapper, _, _ = _make_playwright_wrapper()
        assert wrapper.is_cdp is False

    def test_is_cdp_defaults_to_false_selenium(self):
        wrapper, _ = _make_selenium_wrapper()
        assert wrapper.is_cdp is False

    def test_is_cdp_can_be_set_true_playwright(self):
        wrapper, _, _ = _make_playwright_wrapper(is_cdp=True)
        assert wrapper.is_cdp is True

    def test_is_cdp_can_be_set_true_selenium(self):
        wrapper, _ = _make_selenium_wrapper(is_cdp=True)
        assert wrapper.is_cdp is True


class TestPlayDriverCdpQuit:

    def test_cdp_quit_suppresses_page_close_error(self):
        wrapper, mock_page, mock_context = _make_playwright_wrapper(is_cdp=True)
        mock_page.close = MagicMock(side_effect=PlaywrightError('Target page closed'))
        mock_context.close = MagicMock()

        wrapper.quit(silent=True)
        mock_page.close.assert_called_once()

    def test_cdp_quit_suppresses_context_close_error(self):
        wrapper, mock_page, mock_context = _make_playwright_wrapper(is_cdp=True)
        mock_page.close = MagicMock()
        mock_context.close = MagicMock(side_effect=PlaywrightError('Context closed'))

        wrapper.quit(silent=True)
        mock_context.close.assert_called_once()

    def test_cdp_quit_skips_tracing(self):
        wrapper, _, mock_context = _make_playwright_wrapper(is_cdp=True)
        wrapper.quit(silent=True, trace_path='trace.zip')
        mock_context.tracing.stop.assert_not_called()

    def test_non_cdp_quit_calls_tracing(self):
        wrapper, mock_page, mock_context = _make_playwright_wrapper(is_cdp=False)
        mock_page.close = MagicMock()
        mock_context.close = MagicMock()
        wrapper.quit(silent=True, trace_path='trace.zip')
        mock_context.tracing.stop.assert_called_once_with(path='trace.zip')

    def test_non_cdp_quit_propagates_close_error(self):
        wrapper, mock_page, mock_context = _make_playwright_wrapper(is_cdp=False)
        mock_page.close = MagicMock(side_effect=PlaywrightError('Unexpected error'))
        mock_context.tracing.stop = MagicMock()

        with pytest.raises(PlaywrightError):
            wrapper.quit(silent=True)


class TestCoreDriverCdpQuit:

    def test_cdp_quit_suppresses_webdriver_error(self):
        wrapper, driver_instance = _make_selenium_wrapper(is_cdp=True)
        driver_instance.quit = MagicMock(side_effect=SeleniumWebDriverException('Browser already closed'))

        wrapper.quit(silent=True)
        driver_instance.quit.assert_called_once()

    def test_non_cdp_quit_propagates_webdriver_error(self):
        wrapper, driver_instance = _make_selenium_wrapper(is_cdp=False)
        driver_instance.quit = MagicMock(side_effect=SeleniumWebDriverException('Unexpected error'))

        with pytest.raises(SeleniumWebDriverException):
            wrapper.quit(silent=True)


class TestPlayDriverViewportNullSafe:

    def test_get_inner_window_size_returns_zero_when_viewport_none(self):
        wrapper, mock_page, _ = _make_playwright_wrapper()
        type(mock_page).viewport_size = PropertyMock(return_value=None)

        size = wrapper.get_inner_window_size()
        assert size.width == 0
        assert size.height == 0

    def test_get_inner_window_size_returns_values_when_viewport_set(self):
        wrapper, mock_page, _ = _make_playwright_wrapper()
        type(mock_page).viewport_size = PropertyMock(return_value={'width': 1920, 'height': 1080})

        size = wrapper.get_inner_window_size()
        assert size.width == 1920
        assert size.height == 1080
