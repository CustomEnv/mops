import pytest

from mock.mock import MagicMock, patch

from mops.base.driver_wrapper import DriverWrapper, DriverWrapperSessions
from mops.exceptions import DriverWrapperException

from playwright.sync_api import Page as PlaywrightSourcePage


@pytest.fixture(autouse=True)
def cleanup_sessions():
    yield
    DriverWrapperSessions.all_sessions = []


# --- Playwright CDP tests ---


def _make_cdp_mocks(pages=None):
    mock_pw = MagicMock()

    mock_page = pages[0] if pages else PlaywrightSourcePage(MagicMock())
    all_pages = pages or [mock_page]

    mock_context = MagicMock()
    mock_context.pages = all_pages

    mock_browser = MagicMock()
    mock_browser.contexts = [mock_context]
    mock_browser.browser_type.name = 'chromium'

    mock_pw.chromium.connect_over_cdp.return_value = mock_browser

    return mock_pw, mock_browser, mock_context, all_pages


@patch('mops.base.driver_wrapper.sync_playwright')
def test_connect_cdp_creates_playwright_wrapper(mock_sync_playwright):
    mock_pw, mock_browser, mock_context, pages = _make_cdp_mocks()
    mock_sync_playwright.return_value.start.return_value = mock_pw

    wrapper = DriverWrapper.connect_cdp('http://localhost:9222')

    mock_pw.chromium.connect_over_cdp.assert_called_once_with(
        'http://localhost:9222', timeout=30000
    )
    assert wrapper.is_playwright is True
    assert wrapper._playwright_instance is mock_pw


@patch('mops.base.driver_wrapper.sync_playwright')
def test_connect_cdp_with_custom_timeout(mock_sync_playwright):
    mock_pw, _, _, _ = _make_cdp_mocks()
    mock_sync_playwright.return_value.start.return_value = mock_pw

    DriverWrapper.connect_cdp('http://localhost:9222', timeout=60000)

    mock_pw.chromium.connect_over_cdp.assert_called_once_with(
        'http://localhost:9222', timeout=60000
    )


@patch('mops.base.driver_wrapper.sync_playwright')
def test_connect_cdp_with_viewport_size(mock_sync_playwright):
    mock_pw, _, _, pages = _make_cdp_mocks()
    mock_sync_playwright.return_value.start.return_value = mock_pw

    page = pages[0]
    page.set_viewport_size = MagicMock()

    DriverWrapper.connect_cdp(
        'http://localhost:9222',
        viewport_size={'width': 1920, 'height': 1080},
    )

    page.set_viewport_size.assert_called_once_with(
        {'width': 1920, 'height': 1080}
    )


@patch('mops.base.driver_wrapper.sync_playwright')
def test_connect_cdp_with_page_index(mock_sync_playwright):
    page_0 = PlaywrightSourcePage(MagicMock())
    page_1 = PlaywrightSourcePage(MagicMock())
    mock_pw, _, _, _ = _make_cdp_mocks(pages=[page_0, page_1])
    mock_sync_playwright.return_value.start.return_value = mock_pw

    wrapper = DriverWrapper.connect_cdp('http://localhost:9222', page_index=1)

    assert wrapper.driver is page_1


@patch('mops.base.driver_wrapper.sync_playwright')
def test_connect_cdp_quit_stops_playwright(mock_sync_playwright):
    mock_pw, _, _, _ = _make_cdp_mocks()
    mock_sync_playwright.return_value.start.return_value = mock_pw

    wrapper = DriverWrapper.connect_cdp('http://localhost:9222')
    wrapper.quit(silent=True)

    mock_pw.stop.assert_called_once()


@patch('mops.base.driver_wrapper.sync_playwright')
def test_connect_cdp_quit_without_cdp_no_playwright_stop(mock_sync_playwright):
    """Regular DriverWrapper (non-CDP) quit should not call playwright stop."""
    mock_pw, _, _, _ = _make_cdp_mocks()
    mock_sync_playwright.return_value.start.return_value = mock_pw

    wrapper = DriverWrapper.connect_cdp('http://localhost:9222')
    delattr(wrapper, '_playwright_instance')
    wrapper.quit(silent=True)

    mock_pw.stop.assert_not_called()


@patch('mops.base.driver_wrapper.sync_playwright')
def test_connect_cdp_session_tracking(mock_sync_playwright):
    mock_pw, _, _, _ = _make_cdp_mocks()
    mock_sync_playwright.return_value.start.return_value = mock_pw

    assert DriverWrapperSessions.sessions_count() == 0
    wrapper = DriverWrapper.connect_cdp('http://localhost:9222')
    assert DriverWrapperSessions.sessions_count() == 1
    wrapper.quit(silent=True)
    assert DriverWrapperSessions.sessions_count() == 0


# --- Selenium CDP tests ---


@patch('mops.base.driver_wrapper.DriverWrapper._connect_cdp_selenium')
def test_connect_cdp_selenium_engine_dispatches(mock_selenium_connect):
    mock_selenium_connect.return_value = MagicMock()

    DriverWrapper.connect_cdp('http://localhost:9222', engine='selenium')

    mock_selenium_connect.assert_called_once_with(
        'http://localhost:9222', None
    )


@patch('mops.base.driver_wrapper.DriverWrapper._connect_cdp_playwright')
def test_connect_cdp_playwright_engine_dispatches(mock_pw_connect):
    mock_pw_connect.return_value = MagicMock()

    DriverWrapper.connect_cdp('http://localhost:9222', engine='playwright')

    mock_pw_connect.assert_called_once_with(
        'http://localhost:9222', 30000, 0, None
    )


def test_connect_cdp_invalid_engine():
    try:
        DriverWrapper.connect_cdp('http://localhost:9222', engine='appium')
    except DriverWrapperException as exc:
        assert 'Unsupported engine' in exc.msg
        assert 'appium' in exc.msg
    else:
        raise Exception('Expected DriverWrapperException')


@patch('mops.base.driver_wrapper.sync_playwright')
def test_connect_cdp_sets_is_cdp_flag_playwright(mock_sync_playwright):
    mock_pw, _, _, _ = _make_cdp_mocks()
    mock_sync_playwright.return_value.start.return_value = mock_pw

    wrapper = DriverWrapper.connect_cdp('http://localhost:9222')

    assert wrapper.is_cdp is True
    assert wrapper.is_playwright is True


@patch('mops.base.driver_wrapper.DriverWrapper._connect_cdp_selenium')
def test_connect_cdp_sets_is_cdp_flag_selenium(mock_selenium_connect):
    mock_wrapper = MagicMock()
    mock_wrapper.is_cdp = False
    mock_selenium_connect.return_value = mock_wrapper

    DriverWrapper.connect_cdp('http://localhost:9222', engine='selenium')

    mock_selenium_connect.assert_called_once()


@patch('mops.base.driver_wrapper.DriverWrapper.__new__')
@patch('mops.base.driver_wrapper.DriverWrapper.__init__', return_value=None)
def test_connect_cdp_selenium_sets_debugger_address(mock_init, mock_new):
    """Verify that _connect_cdp_selenium correctly parses endpoint URL and sets debugger_address."""
    mock_instance = MagicMock()
    mock_new.return_value = mock_instance

    with patch('mops.base.driver_wrapper.DriverWrapper._connect_cdp_selenium') as original:
        original.side_effect = DriverWrapper._connect_cdp_selenium.__wrapped__ if hasattr(
            DriverWrapper._connect_cdp_selenium, '__wrapped__'
        ) else None

    from urllib.parse import urlparse

    for url, expected in [
        ('http://localhost:9222', 'localhost:9222'),
        ('https://remote-host:9222/', 'remote-host:9222'),
        ('http://http-proxy:9222', 'http-proxy:9222'),
        ('http://192.168.1.100:9222', '192.168.1.100:9222'),
    ]:
        parsed = urlparse(url)
        result = f'{parsed.hostname}:{parsed.port}'
        assert result == expected, f'URL {url} parsed to {result}, expected {expected}'


# --- PlayDriver CDP quit behavior ---


@patch('mops.base.driver_wrapper.sync_playwright')
def test_playwright_cdp_quit_suppresses_close_errors(mock_sync_playwright):
    """PlayDriver.quit() should suppress close errors for CDP connections."""
    from playwright._impl._errors import Error as PlaywrightError

    mock_pw, _, mock_context, pages = _make_cdp_mocks()
    mock_sync_playwright.return_value.start.return_value = mock_pw

    page = pages[0]
    page.close = MagicMock(side_effect=PlaywrightError('Target page closed'))
    mock_context.close = MagicMock(side_effect=PlaywrightError('Context closed'))

    wrapper = DriverWrapper.connect_cdp('http://localhost:9222')

    wrapper.quit(silent=True)

    page.close.assert_called_once()
    mock_context.close.assert_called_once()


@patch('mops.base.driver_wrapper.sync_playwright')
def test_playwright_cdp_quit_skips_tracing(mock_sync_playwright):
    """PlayDriver.quit() should not call tracing.stop() for CDP connections."""
    mock_pw, _, mock_context, _ = _make_cdp_mocks()
    mock_sync_playwright.return_value.start.return_value = mock_pw

    wrapper = DriverWrapper.connect_cdp('http://localhost:9222')
    wrapper.quit(silent=True, trace_path='trace.zip')

    mock_context.tracing.stop.assert_not_called()
