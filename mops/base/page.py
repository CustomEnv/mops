from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

from appium.webdriver.webdriver import WebDriver as AppiumDriver
from playwright.sync_api import Page as PlaywrightDriver
from selenium.webdriver.remote.webdriver import WebDriver as SeleniumDriver

from mops.abstraction.page_abc import PageABC
from mops.base.element import Element
from mops.exceptions import DriverWrapperException
from mops.mixins.driver_mixin import DriverMixin, get_driver_wrapper_from_object
from mops.mixins.internal_mixin import InternalMixin
from mops.playwright.play_page import PlayPage
from mops.selenium.pages.mobile_page import MobilePage
from mops.selenium.pages.web_page import WebPage
from mops.utils.internal_utils import (
    WAIT_PAGE,
    extract_named_objects,
    initialize_objects,
)
from mops.utils.logs import Logging
from mops.utils.previous_object_driver import PreviousObjectDriver, set_instance_frame

if TYPE_CHECKING:
    from typing import Self

    from mops.base.driver_wrapper import DriverWrapper
    from mops.mixins.objects.locator import Locator


class Page(DriverMixin, InternalMixin, Logging, PageABC):
    """
    Represents a page in a web or mobile application.

    The page object encapsulates the necessary logic for interacting with a page using different
    drivers (Appium, Selenium, Playwright).

    This class should be defined for each specific page in the application,
    encapsulating the page's :class:`.Element` and groups of elements under :class:`.Group`.

    It supports dynamic driver selection and element management based on the current driver.
    """

    _object = 'page'
    _base_cls: type[PlayPage, MobilePage, WebPage]

    url: str
    log_locator: str | None = None
    locator_type: str | None = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        """Create a new Page instance and set the frame for multi-session tracking."""
        instance = super().__new__(cls)
        set_instance_frame(instance)
        return instance

    def __repr__(self) -> str:
        """Return a string representation of this Page."""
        return self._repr_builder()

    def __init__(
        self,
        locator: Locator | str = '',
        name: str = '',
        driver_wrapper: DriverWrapper | Any = None,
    ):
        """
        Initialize a Page based on the current driver.

        :param locator: The anchor locator of the page. `.LocatorType` is optional.
        :type locator: typing.Union[Locator, str]
        :param name: The name of the page, used for logging and identification purposes.
        :type name: str
        :param driver_wrapper: The :class:`.DriverWrapper` instance or
         an object containing it to be used for entire page.
        :type driver_wrapper: typing.Union[DriverWrapper, typing.Any]
        """
        self.driver_wrapper = get_driver_wrapper_from_object(driver_wrapper)

        self.locator = locator
        self.name = name

        self._modify_page_driver_wrapper(driver_wrapper)
        self._modify_sub_elements()
        self._safe_setter('__base_obj_id', id(self))

        self.__init_base_class__()

    def __init_base_class__(self) -> None:
        """
        Initialise base class according to current driver, and set his methods

        :return: None
        """
        if self._driver_is_instance(PlaywrightDriver):
            self._base_cls = PlayPage
        elif self._driver_is_instance(AppiumDriver):
            self._base_cls = MobilePage
        elif self._driver_is_instance(SeleniumDriver):
            self._base_cls = WebPage
        else:
            msg = (
                f'Cannot initialize {Page.__name__}: '
                f'unsupported driver type "{type(self.driver).__name__}". '
                f'Expected Playwright, Appium or Selenium driver instance'
            )
            raise DriverWrapperException(
                msg,
            )

        self._set_static(self._base_cls)
        self._base_cls.__init__(self)

    @cached_property
    def anchor(self) -> Element:
        """
        Return the anchor element of the page

        :return: :base:`.Element`
        """
        anchor = Element(self.locator, name=self.name, driver_wrapper=self.driver_wrapper)
        self.locator = anchor.locator
        self.name = anchor.name
        self.locator_type = anchor.locator_type
        self.log_locator = anchor.log_locator

        return anchor

    # Following methods works same for both Selenium/Appium and Playwright APIs using internal methods

    def reload_page(self, wait_page_load: bool = True) -> Page:
        """
        Reload the current page and optionally wait for the page to fully load.

        :param wait_page_load: If :obj:`True`, waits until the page is fully loaded and an
          anchor element is visible. Defaults to :obj:`True`.
        :type wait_page_load: bool
        :return: :obj:`Page` - The current instance of the page object.
        """
        self.log(f'Reload "{self.name}" page')
        self.driver_wrapper.refresh()

        if wait_page_load:
            self.wait_page_loaded()

        return self

    def open_page(self, url: str = '') -> Page:
        """
        Open a page using the given URL, or use the default URL from the page class if no URL is provided.

        :param url: The URL to navigate to. If not provided, the default URL from the page class will be used.
        :type url: str
        :return: :obj:`Page` - The current instance of the page object.
        """
        url = url or self.url
        self.driver_wrapper.get(url)
        self.wait_page_loaded()
        return self

    def wait_page_loaded(self, silent: bool = False, timeout: float = WAIT_PAGE) -> Page:
        """
        Wait until the page is fully loaded by checking the visibility of the anchor element and other page elements.

        Waits for the anchor element to become visible, and depending on the configuration of each page element,
        it waits for either their visibility or to be hidden.

        :param silent: If :obj:`True`, suppresses logging during the waiting process. Defaults to :obj:`False`.
        :type silent: bool
        :param timeout: The maximum time (in seconds) to wait for the page or elements to load. Defaults to `WAIT_PAGE`.
        :type timeout: Union[int, float]
        :return: :obj:`Page` - The current instance of the page object.
        """
        if not silent:
            self.log(f'Wait until page "{self.name}" loaded')

        self.anchor.wait_visibility(timeout=timeout, silent=True)

        for element in self.sub_elements.values():
            if element.wait is False:
                element.wait_hidden(timeout=timeout, silent=True)
            elif element.wait is True:
                element.wait_visibility(timeout=timeout, silent=True)
        return self

    def is_page_opened(self, with_elements: bool = False, with_url: bool = False) -> bool:
        """
        Check whether the current page is opened.

        :param with_elements: If `True`, verify the page is opened by checking specific elements.
        :type with_elements: bool
        :param with_url: If `True`, verify the page is opened by checking the URL.
        :type with_url: bool
        :return: :obj:`bool` - `True` if the page is opened, otherwise `False`.
        """
        result = True

        if with_elements:
            for element in self.sub_elements.values():
                if element.wait:
                    result &= element.is_displayed(silent=True)
                    if not result:
                        self.log(f'Element "{element.name}" is not displayed', level='debug')

        result &= self.anchor.is_displayed()

        if with_url:
            result &= self.driver_wrapper.current_url == self.url

        return result

    def _modify_sub_elements(self) -> None:
        """
        Initialize attributes with type == Element.
        Required for classes with base == Page.
        """
        self.sub_elements = extract_named_objects(self, Element)
        initialize_objects(self, self.sub_elements)

    def _modify_page_driver_wrapper(self, driver_wrapper: Any) -> None:
        """
        Modify current object if driver_wrapper is not given. Required for Page that placed into functions:
        - sets driver from previous object
        """
        if not driver_wrapper:
            PreviousObjectDriver().set_driver_from_previous_object(self)
