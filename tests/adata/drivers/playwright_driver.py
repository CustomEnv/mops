from playwright.sync_api import sync_playwright

from mops.mixins.objects.driver import Driver
from tests.adata.drivers.driver_entities import DriverEntities


class PlaywrightDriver:

    _instance = None

    @classmethod
    def create_playwright_driver(cls, entities: DriverEntities) -> Driver:
        if cls._instance is None:
            browser = cls.start_session(entities.driver_name)
            cls._instance = browser.launch(headless=entities.config.getoption('headless'))

        context = cls._instance.new_context()
        driver = context.new_page()
        context.set_default_timeout(10000)

        return Driver(driver=driver, context=context, instance=cls._instance)

    @classmethod
    def start_session(cls, driver_name):
        playwright = sync_playwright().start()

        drivers = {
            'chrome': playwright.chromium,
            'firefox': playwright.firefox,
            'safari': playwright.webkit,
        }

        return drivers.get(driver_name)
