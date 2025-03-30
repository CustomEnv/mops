from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from mops.abstraction.mixin_abc import MixinABC
from mops.utils.internal_utils import WAIT_PAGE

if TYPE_CHECKING:
    from mops.base.element import Element
    from mops.base.page import Page


class PageABC(MixinABC, ABC):

    anchor: Element

    def reload_page(self, wait_page_load: bool = True) -> Page:
        """
        Reload the current page and optionally wait for the page to fully load.

        :param wait_page_load: If :obj:`True`, waits until the page is fully loaded and an
          anchor element is visible. Defaults to :obj:`True`.
        :type wait_page_load: bool
        :return: :obj:`Page` - The current instance of the page object.
        """
        raise NotImplementedError

    def open_page(self, url: str = '') -> Page:
        """
        Open a page using the given URL, or use the default URL from the page class if no URL is provided.

        :param url: The URL to navigate to. If not provided, the default URL from the page class will be used.
        :type url: str
        :return: :obj:`Page` - The current instance of the page object.
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def is_page_opened(self, with_elements: bool = False, with_url: bool = False) -> bool:
        """
        Check whether the current page is opened.

        :param with_elements: If `True`, verify the page is opened by checking specific elements.
        :type with_elements: bool
        :param with_url: If `True`, verify the page is opened by checking the URL.
        :type with_url: bool
        :return: :obj:`bool` - `True` if the page is opened, otherwise `False`.
        """
        raise NotImplementedError

    def swipe(
            self,
            start_x: int,
            start_y: int,
            end_x: int,
            end_y: int,
            duration: int = 0,
            sleep: float = 0,
    ) -> Page:
        """
        Appium only: Swipe from one point to another, with an optional duration and post-swipe delay.

        :param start_x: The x-coordinate at which to start the swipe.
        :type start_x: int
        :param start_y: The y-coordinate at which to start the swipe.
        :type start_y: int
        :param end_x: The x-coordinate at which to end the swipe.
        :type end_x: int
        :param end_y: The y-coordinate at which to end the swipe.
        :type end_y: int
        :param duration: The duration of the swipe in milliseconds.
        :type duration: int
        :param sleep: The delay (in seconds) after completing the swipe.
        :type sleep: Union[int, float]
        :return: :obj:`Page` - The current instance of the page object.
        """
        raise NotImplementedError

    def swipe_down(self) -> Page:
        """
        Scroll the page downward using a swipe gesture.

        :return: :obj:`Page` - The current instance of the page object.
        """
        raise NotImplementedError

    def swipe_up(self) -> Page:
        """
        Scroll the page upward using a swipe gesture.

        :return: :obj:`Page` - The current instance of the page object.
        """
        raise NotImplementedError
