from __future__ import annotations

from logging import info

from dyatel.dyatel_play.play_driver import PlayDriver
from dyatel.dyatel_play.play_element import PlayElement
from dyatel.dyatel_play.play_utils import get_selenium_completable_locator
from dyatel.internal_utils import get_child_elements


class PlayPage:

    def __init__(self, locator: str, locator_type='', name=''):
        """
        Initializing of web page with playwright driver

        :param locator: anchor locator of page. Can be defined without locator_type
        :param locator_type: specific locator type
        :param name: name of page (will be attached to logs)
        """
        self.locator = get_selenium_completable_locator(locator)
        self.name = name if name else self.locator
        self.locator_type = f'{locator_type}: locator_type does not supported for playwright'
        self.driver = PlayDriver.driver
        self.context = PlayDriver.context
        self.driver_wrapper = PlayDriver(self.driver, initial_page=False)

        self.url = getattr(self, 'url', '')
        self.page_elements = get_child_elements(self, PlayElement)
        for el in self.page_elements:
            if not el.driver:
                el.__init__(locator=el.locator, locator_type=el.locator_type, name=el.name, parent=el.parent)

    def reload_page(self, wait_page_load=True) -> PlayPage:
        """
        Reload current page

        :param wait_page_load: wait until anchor will be element loaded
        :return: self
        """
        info(f'Reload {self.name} page')
        self.driver_wrapper.refresh()
        if wait_page_load:
            self.wait_page_loaded()
        return self

    def open_page(self, url='') -> PlayPage:
        """
        Open page with given url or use url from page class f url isn't given

        :param url: url for navigation
        :return: self
        """
        url = self.url if not url else url
        if not self.is_page_opened():
            self.driver_wrapper.get(url)
            self.wait_page_loaded()
        return self

    def wait_page_loaded(self, silent=False) -> PlayPage:
        """
        Wait until page loaded

        :param silent: erase log
        :return: self
        """
        if not silent:
            info(f'Wait until page "{self.name}" loaded')
        self.context.wait_for_selector(self.locator)
        return self

    def is_page_opened(self) -> bool:
        """
        Check is current page opened or not

        :return: self
        """
        if self.url:
            return self.driver_wrapper.current_url == self.url
        else:
            page_anchor = PlayElement(locator=self.locator, locator_type=self.locator_type, name=self.name)
            return page_anchor.is_displayed()
