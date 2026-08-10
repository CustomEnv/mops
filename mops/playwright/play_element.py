from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

from playwright.sync_api import Error, Locator, Page as PlaywrightPage

from mops.abstraction.element_abc import ElementABC
from mops.exceptions import (
    DriverWrapperException,
    InvalidSelectorException,
    NoSuchElementException,
    NotInitializedException,
)
from mops.mixins.objects.location import Location
from mops.mixins.objects.size import Size
from mops.self_healing.config import get_config
from mops.self_healing.healer import FailedHealingResult, SuccessHealingResult
from mops.self_healing.healer_factory import get_healer
from mops.self_healing.locator_generator import generate_locator_pw
from mops.shared_utils import cut_log_data, get_image
from mops.utils.decorators import healing, retry
from mops.utils.internal_utils import (
    calculate_coordinate_to_click,
    is_element,
    is_group,
)
from mops.utils.logs import Logging
from mops.utils.selector_synchronizer import get_platform_locator, set_playwright_locator

if TYPE_CHECKING:
    from PIL.Image import Image

    from mops.keyboard_keys import KeyboardKeys


class PlayElement(ElementABC, Logging, ABC):
    parent: ElementABC | PlayElement

    _initialized: bool
    _element: Locator = None

    # Element

    @property
    def element(self) -> Locator:
        """
        Get playwright Locator object

        :param: args: args from Locator object
        :param: kwargs: kwargs from Locator object
        :return: Locator
        """
        if not self._initialized:
            msg = (
                f'{self!r} object is not initialized. '
                'Try to initialize base object first or call it directly as a method'
            )
            raise NotInitializedException(msg)

        element = self._element

        if not element:
            driver = self._get_base()
            element = driver.locator(self.locator)

        return element

    @element.setter
    def element(self, base_element: Locator | None) -> None:
        """
        Element object setter. Try to avoid usage of this function

        :param: play_element: playwright Locator object
        """
        self._element = base_element

    @property
    def all_elements(self) -> list[PlayElement] | list[Any]:
        """
        Returns a list of all matching elements.

        :return: A list of wrapped :class:`PlayElement` objects.
        """
        return self._get_all_elements(self.element.all())

    # Element interaction

    @healing
    def click(self, *, force_wait: bool = True, **kwargs: Any) -> PlayElement:
        """
        Clicks on the element.

        :param force_wait: If :obj:`True`, waits for element visibility before clicking.
        :type force_wait: bool

        **Selenium/Appium:**

        Selenium Safari using js click instead.

        :param kwargs: compatibility arg for playwright

        **Playwright:**

        :param kwargs: `any kwargs params from source API <https://playwright.dev/python/docs/api/class-locator#locator-click>`_

        :return: :class:`PlayElement`
        """
        self.log(f'Click into "{self.name}"')

        if force_wait:
            self.wait_visibility(silent=True)

        try:
            if self.driver_wrapper.is_mobile_resolution:
                self._first_element.tap(**kwargs)
            else:
                self._first_element.click(**kwargs)
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc

        return self

    def click_outside(self, x: int = -5, y: int = -5) -> PlayElement:
        """
        Perform a click outside the current element, by default 5px left and above it.

        :param x: Horizontal offset from the element to click.
        :type x: int
        :param y: Vertical offset from the element to click.
        :type y: int
        :return: :class:`PlayElement`
        """
        self.log(f'Click outside from "{self.name}"')

        self._first_element.click(position={'x': float(x), 'y': float(y)}, force=True)
        return self

    def click_into_center(self, silent: bool = False) -> PlayElement:
        """
        Clicks at the center of the element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        if not self.is_fully_visible(silent=True):
            self.scroll_into_view()

        x, y = calculate_coordinate_to_click(self, 0, 0)

        if not silent:
            self.log(f'Click into the center (x: {x}, y: {y}) for "{self.name}"')

        self.driver_wrapper.click_by_coordinates(x=x, y=y, silent=True)
        return self

    @healing
    def type_text(self, text: str | KeyboardKeys, silent: bool = False) -> PlayElement:
        """
        Types text into the element.

        :param text: The text to be typed or a keyboard key.
        :type text: str, :class:`KeyboardKeys`
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        text = str(text)

        if not silent:
            self.log(f'Type text "{cut_log_data(text)}" into "{self.name}"')

        try:
            self._first_element.type(text=text)
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc
        return self

    @healing
    def type_slowly(self, text: str, sleep_gap: float = 0.05, silent: bool = False) -> PlayElement:
        """
        Types text into the element slowly with a delay between keystrokes.

        :param text: The text to be typed.
        :type text: str
        :param sleep_gap: Delay between keystrokes in seconds.
        :type sleep_gap: float
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        if not silent:
            self.log(f'Type text {cut_log_data(text)} into "{self.name}"')

        try:
            self._first_element.type(text=text, delay=sleep_gap)
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc
        return self

    @healing
    def clear_text(self, silent: bool = False) -> PlayElement:
        """
        Clear the text of the element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        if not silent:
            self.log(f'Clear text in "{self.name}"')

        try:
            self._first_element.fill('')
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc
        return self

    @healing
    def hover(self, silent: bool = False) -> PlayElement:
        """
        Hover the mouse over the current element.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`PlayElement`
        """
        if not silent:
            self.log(f'Hover over "{self.name}"')

        try:
            self._first_element.hover()
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc
        return self

    def hover_outside(self, x: int = 0, y: int = -5) -> PlayElement:
        """
        Hover the mouse outside the current element, by default 5px above it.

        :param x: Horizontal offset from the element to hover.
        :type x: int
        :param y: Vertical offset from the element to hover.
        :type y: int
        :return: :class:`PlayElement`
        """
        self.log(f'Hover outside from "{self.name}"')
        self._first_element.hover(position={'x': float(x), 'y': float(y)}, force=True)
        return self

    @healing
    def check(self) -> PlayElement:
        """
        Check the checkbox element.

        :return: :class:`PlayElement`
        """
        try:
            self._first_element.check()
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc
        return self

    @healing
    def uncheck(self) -> PlayElement:
        """
        Unchecks the checkbox element.

        :return: :class:`PlayElement`
        """
        try:
            self._first_element.uncheck()
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc
        return self

    # Element state

    @healing
    def screenshot_image(self, screenshot_base: bytes | None = None) -> Image:
        """
        Return a :class:`PIL.Image.Image` object representing the screenshot of the web element.
        Appium iOS: Take driver screenshot and crop manually element from it

        :param screenshot_base: Screenshot binary data (optional).
          If :obj:`None` is provided then takes a new screenshot
        :type screenshot_base: bytes
        :return: :class:`PIL.Image.Image`
        """
        screenshot_base = screenshot_base or self.screenshot_base
        return get_image(screenshot_base)

    @property
    @healing
    def screenshot_base(self) -> bytes:
        """
        Returns the binary screenshot data of the element.

        :return: :class:`bytes` - screenshot binary
        """
        try:
            return self._first_element.screenshot()
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc

    @property
    @healing
    def text(self) -> str:
        """
        Returns the text of the element.

        :return: :class:`str` - element text
        """
        try:
            return self.inner_text
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc

    @property
    @healing
    def inner_text(self) -> str:
        """
        Returns the inner text of the element.

        :return: :class:`str` - element inner text
        """
        try:
            return self._first_element.inner_text()
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc

    @property
    @healing
    def value(self) -> str:
        """
        Returns the value of the element.

        :return: :class:`str` - element value
        """
        try:
            return self._first_element.input_value()
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc

    def is_available(self) -> bool:
        """
        Check if the element is available in DOM tree.

        :return: :class:`bool` - :obj:`True` if present in DOM
        """
        result = bool(len(self.element.element_handles()))
        if result:
            self._save_snapshot(self._first_element)
        return result

    def is_displayed(self, silent: bool = False) -> bool:
        """
        Check if the element is displayed.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        if not silent:
            self.log(f'Check visibility of "{self.name}"')

        try:
            result = self._first_element.is_visible()
        except Error as exc:
            raise InvalidSelectorException(exc.message) from exc
        else:
            if result:
                self._save_snapshot(self._first_element)
            return result

    def is_hidden(self, silent: bool = False) -> bool:
        """
        Check if the element is hidden.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool`
        """
        if not silent:
            self.log(f'Check invisibility of "{self.name}"')

        return self._first_element.is_hidden()

    @healing
    def get_attribute(self, attribute: str, silent: bool = False) -> str:
        """
        Retrieve a specific attribute from the current element.

        :param attribute: The name of the attribute to retrieve, such as 'value', 'innerText', 'textContent', etc.
        :type attribute: str
        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`str` - The value of the specified attribute.
        """
        if not silent:
            self.log(f'Get "{attribute}" from "{self.name}"')

        try:
            return self._first_element.get_attribute(attribute)
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc

    def get_all_texts(self, silent: bool = False) -> list:
        """
        Retrieve text content from all matching elements.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`list` of :class:`str` - A list containing the text content of all matching elements.
        """
        if not silent:
            self.log(f'Get all texts from "{self.name}"')

        return self.element.all_text_contents()

    def get_elements_count(self, silent: bool = False) -> int:
        """
        Get the count of matching elements.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`int` - The number of matching elements.
        """
        if not silent:
            self.log(f'Get elements count of "{self.name}"')

        return len(self.all_elements)

    @retry(AttributeError)
    def get_rect(self) -> dict:
        """
        Retrieve the size and position of the element as a dictionary.

        :return: :class:`dict` - A dictionary {'x', 'y', 'width', 'height'} of the element.
        """
        sorted_items: list = sorted(self.element.bounding_box().items(), reverse=True)
        return dict(sorted_items)

    @property
    @retry(TypeError)
    def size(self) -> Size:
        """
        Get the size of the current element, including width and height.

        :return: :class:`.Size` - An object representing the element's dimensions.
        """
        box = self.element.first.bounding_box()
        return Size(width=box['width'], height=box['height'])

    @property
    @retry(TypeError)
    def location(self) -> Location:
        """
        Get the location of the current element, including the x and y coordinates.

        :return: :class:`Location` - An object representing the element's position.
        """
        box = self.element.first.bounding_box()
        return Location(x=box['x'], y=box['y'])

    @healing
    def is_enabled(self, silent: bool = False) -> bool:
        """
        Check if the current element is enabled.

        :param silent: If :obj:`True`, suppresses logging.
        :type silent: bool
        :return: :class:`bool` - :obj:`True` if the element is enabled, :obj:`False` otherwise.
        """
        if not silent:
            self.log(f'Check is element "{self.name}" enabled')

        try:
            return self._first_element.is_enabled()
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc

    @healing
    def is_checked(self) -> bool:
        """
        Check if a checkbox or radio button is selected.

        :return: :class:`bool` - :obj:`True` if the checkbox or radio button is checked, :obj:`False` otherwise.
        """
        try:
            return self._first_element.is_checked()
        except Error as exc:
            raise NoSuchElementException(str(exc)) from exc

    # Mixin

    def _get_base(self, wait_strategy: bool = True) -> PlaywrightPage | Locator:
        """
        Get driver depends on parent element if available

        :param wait_strategy: Compatibility parameter for the Selenium signature.
            Playwright Locators are lazy so this has no effect.
        :return: driver
        """
        base = self.driver
        if not base:
            msg = "Can't find driver"
            raise DriverWrapperException(msg)

        if self.parent:
            self.log(f'Get element "{self.name}" from parent element "{self.parent.name}"', level='debug')

            if is_group(self.parent) or is_element(self.parent):
                base = self.parent.element

        return base

    @property
    def _first_element(self) -> Locator:
        """
        Get first element

        :return: first element
        """
        return self.element.first

    def _set_locator(self) -> None:
        self.locator = get_platform_locator(self)
        set_playwright_locator(self)
        self._is_locator_configured = True

    # Self-healing

    @staticmethod
    def _parse_healed_locator_pw(healed_locator: str) -> str:
        """Strip the ``xpath=`` prefix from a healed locator for Playwright use."""
        if healed_locator.startswith('xpath='):
            return healed_locator[len('xpath=') :]
        return healed_locator

    def _save_snapshot(self, locator_element: Locator) -> None:
        """Save a DOM snapshot for the current element if snapshot saving is enabled."""
        config = get_config()
        if config.save_snapshots and config.storage:
            try:
                config.storage.save_from_element(self, locator_element, self.driver_wrapper)
            except Exception as exc:  # noqa: BLE001
                self.log(f'Failed to save snapshot for "{self.name}": {exc}', level='debug')

    def _attempt_healing(self) -> SuccessHealingResult | None:
        """Attempt to heal a failed element lookup using the self-healing subsystem.

        :return: :class:`SuccessHealingResult` if a suitable candidate was found,
            :obj:`None` otherwise.
        """
        try:
            healer = get_healer()
            storage = get_config().storage
            locator_key = storage.extract_full_locator_key(self)
            result = healer.heal(
                element_name=self.name,
                locator_key=locator_key,
                locator=self.locator,
                driver_wrapper=self.driver_wrapper,
                find_elements_fn=lambda tag: self.driver.locator(tag).all(),
                generate_locator_fn=generate_locator_pw,
            )
            if type(result) is SuccessHealingResult:
                return result
        except Exception as exc:  # noqa: BLE001
            self.log(f'Self-healing failed with unexpected exception: {exc}', level='warning')
            return None

    def _try_healed_locators(self, result: SuccessHealingResult) -> None:
        """Try each healed locator candidate and persist the first working one.

        A healing attempt always ends with a terminal callback: ``on_healing_success``
        when a candidate passes DOM verification, or ``on_healing_failure`` otherwise
        (including when verification itself fails or cannot be performed).

        :param result: The healing result containing candidate locators.
        :raises NoSuchElementException: If no candidate locator resolves to an element.
        """
        config = get_config()
        try:
            base = self._get_base(wait_strategy=False)
            for locator_str in result.healed_locators_candidates:
                selector = self._parse_healed_locator_pw(locator_str)
                try:
                    candidate = base.locator(selector)
                    if candidate.count() > 0:
                        result.healed_locator = locator_str
                        self.locator = selector
                        self._element = candidate
                        self.log(f'Self-healing: healed "{self.name}" with locator "{locator_str}"')
                        # Fire success callback AFTER locator is verified against DOM
                        if config.on_healing_success:
                            config.on_healing_success(result)
                        return
                except Error:
                    continue
            error = 'All healed locator candidates failed DOM verification'
        except Exception as exc:  # noqa: BLE001
            error = str(exc)

        # Terminal failure — none of the candidates passed DOM verification
        if config.on_healing_failure:
            config.on_healing_failure(
                FailedHealingResult(
                    element_name=result.element_name,
                    locator_key='',
                    locator=result.original_locator,
                    reason='no-verified-locator',
                    error=error,
                    best_score=result.score,
                    score_threshold=config.score_threshold,
                    breakdown=result.breakdown,
                )
            )

        msg = error or 'Healed locator candidates did not match any element'
        raise NoSuchElementException(msg)

    def _apply_healing(self) -> bool:
        """Attempt healing and persist the first working locator.

        Called by :func:`@healing <mops.utils.decorators.healing>` and
        :func:`@healing_after_wait <mops.utils.decorators.healing_after_wait>`.

        :return: :obj:`True` if a healed locator was found and applied.
        """
        result = self._attempt_healing()
        if not result:
            return False
        try:
            self._try_healed_locators(result)
        except NoSuchElementException:
            return False
        return True

    def _heal_after_wait(self) -> bool:
        """Attempt healing after a wait condition timed out.

        :return: :obj:`True` if a working locator was found.
        """
        return self._apply_healing()
