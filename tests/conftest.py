import os

import pytest
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions

from mops.base.driver_wrapper import DriverWrapper
from mops.mixins.objects.driver import Driver
from mops.mixins.objects.size import Size
from mops.utils.logs import driver_wrapper_logs_settings
from mops.visual_comparison import VisualComparison
from tests.adata.drivers.driver_entities import DriverEntities
from tests.adata.drivers.driver_factory import DriverFactory
from tests.adata.pages.PopupsPage import PopupsPage
from tests.adata.pages.colored_blocks_page import ColoredBlocksPage
from tests.adata.pages.expected_condition_page import ExpectedConditionPage
from tests.adata.pages.forms_page import FormsPage
from tests.adata.pages.frames_page import FramesPage
from tests.adata.pages.keyboard_page import KeyboardPage
from tests.adata.pages.progress_bar_page import ProgressBarPage
from tests.adata.pages.mouse_event_page import MouseEventPage
from tests.adata.pages.pizza_order_page import PizzaOrderPage
from tests.adata.pages.playground_main_page import PlaygroundMainPage, SecondPlaygroundMainPage
from tests.adata.pytest_utils import skip_platform


driver_wrapper_logs_settings()

DESKTOP_WINDOW_SIZE = Size(1024, 900)


def pytest_addoption(parser):
    parser.addoption('--headless', action='store_true', help='Run in headless mode')
    parser.addoption('--driver', default='chrome', help='Browser name')
    parser.addoption('--platform', default='selenium', help='Platform name')
    parser.addoption('--gr', action='store_true', help='Generate reference images in visual tests')
    parser.addoption('--sv', action='store_true', help='Generate reference images in visual tests')
    parser.addoption('--hgr', action='store_true', help='Hard generate reference images in visual tests')
    parser.addoption('--sgr', action='store_true', help='Soft generate reference images in visual tests')
    parser.addoption('--appium-port', default='4723')
    parser.addoption('--appium-ip', default='127.0.0.1')
    parser.addoption('--env', default='local', choices=['local', 'remote'])


@pytest.fixture(scope='session')
def driver_name(request):
    return request.config.getoption('driver').lower()


@pytest.fixture(scope='session')
def platform(request):
    return request.config.getoption('platform').lower()


@pytest.fixture(scope='session')
def driver_entities(request, firefox_options, chrome_options, safari_options, driver_name):
    return DriverEntities(
        request=request,
        driver_name=driver_name,
        selenium_chrome_options=chrome_options,
        selenium_firefox_options=firefox_options,
        selenium_safari_options=safari_options,
        **vars(request.config.option),
    )


@pytest.fixture(scope='session')
def chrome_options(request):
    options = ChromeOptions()
    if request.config.getoption('headless'):
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-allow-origins=*")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    return options


@pytest.fixture(scope='session')
def firefox_options(request):
    options = FirefoxOptions()
    if request.config.getoption('headless'):
        options.add_argument('--headless')
    return options


@pytest.fixture(scope='session')
def safari_options():
    options = SafariOptions()
    options.automatic_inspection = False
    options.automatic_profiling = False
    return options


@pytest.fixture(autouse=True)
def redirect(request):
    # Prints are required for better readability: https://github.com/pytest-dev/pytest/issues/8574
    print()
    yield
    print()
    if DriverWrapper.session.sessions_count() > 0:
        dw = request.getfixturevalue('driver_wrapper')
        dw.get('data:,', silent=True)


@pytest.fixture
def second_driver_wrapper(driver_entities):
    driver = driver_func(driver_entities)
    yield driver
    driver.quit(silent=True)


@pytest.fixture(scope='session')
def driver_wrapper(driver_entities):
    driver = driver_func(driver_entities)
    yield driver
    driver.quit(silent=True)


def driver_func(driver_entities):
    driver: Driver = DriverFactory.create_driver(driver_entities)

    driver_wrapper = DriverWrapper(driver)

    if driver_wrapper.is_desktop:
        driver_wrapper.set_window_size(DESKTOP_WINDOW_SIZE)

    return driver_wrapper


@pytest.fixture(autouse=True)
def visual_comparisons_settings(request):
    VisualComparison.visual_regression_path = os.path.dirname(os.path.abspath(__file__)) + '/adata/visual'
    VisualComparison.visual_reference_generation = request.config.getoption('--gr')
    VisualComparison.hard_visual_reference_generation = request.config.getoption('--hgr')
    VisualComparison.soft_visual_reference_generation = request.config.getoption('--sgr')
    VisualComparison.skip_screenshot_comparison = request.config.getoption('--sv')
    VisualComparison.default_threshold = 0.1
    VisualComparison.test_item = request.node


def pytest_collection_modifyitems(items):
    for item in items:
        skip_platform(
            item=item,
            platform=item.session.config.getoption("--platform"),
            browser=item.session.config.getoption("--driver")
        )


@pytest.fixture
def base_playground_page(driver_wrapper):
    return PlaygroundMainPage().open_page()


@pytest.fixture
def second_playground_page(driver_wrapper):
    return SecondPlaygroundMainPage().open_page()


@pytest.fixture
def colored_blocks_page(driver_wrapper):
    return ColoredBlocksPage().open_page()


@pytest.fixture
def popups_page(driver_wrapper):
    return PopupsPage().open_page()


@pytest.fixture
def pizza_order_page(driver_wrapper):
    return PizzaOrderPage().open_page()


@pytest.fixture
def mouse_event_page(driver_wrapper):
    return MouseEventPage().open_page()


@pytest.fixture
def forms_page(driver_wrapper):
    return FormsPage().open_page()


@pytest.fixture
def expected_condition_page(driver_wrapper):
    return ExpectedConditionPage().open_page().set_min_and_max_wait()


@pytest.fixture
def progressbar_page(driver_wrapper):
    return ProgressBarPage().open_page()


@pytest.fixture
def keyboard_page(driver_wrapper):
    return KeyboardPage().open_page()


@pytest.fixture
def frames_page(driver_wrapper):
    return FramesPage().open_page()
