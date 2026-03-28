from __future__ import annotations

from typing import TYPE_CHECKING

from mops.mixins.capabilities import (
    CUSTOM_BOTTOM_BAR_LOCATOR_CAPABILITY,
    CUSTOM_DONE_BUTTON_LOCATOR_CAPABILITY,
    CUSTOM_TOP_BAR_LOCATOR_CAPABILITY,
)
from mops.mixins.objects.locator import Locator

if TYPE_CHECKING:
    from mops.base.driver_wrapper import DriverWrapper


class NativeContext:
    def __init__(self, driver_wrapper: DriverWrapper) -> None:
        """Initialize NativeContext with the given driver wrapper."""
        self.driver_wrapper = driver_wrapper

    def __enter__(self) -> None:
        """Switch to native app context."""
        self.driver_wrapper.switch_to_native()

    def __exit__(self, *args: object) -> None:
        """Switch back to web context."""
        self.driver_wrapper.switch_to_web()


class NativeSafari:
    _IOS_VERSION_18_2 = 18.2
    _IOS_VERSION_26 = 26.0

    ios_keyboard_hide_button = "//XCUIElementTypeButton[@name='Done']"

    ios_18_bottom_bar_locator = (
        '//*[@name="CapsuleViewController"]/XCUIElementTypeOther/'
        'XCUIElementTypeOther[1]/XCUIElementTypeOther[1]'
    )  # `Tab Bar` at Safari settings
    ios_26_bottom_bar_locator = (
        '//*[@name="CapsuleViewController"]/XCUIElementTypeOther[2]'  # `Compact` at Safari settings
    )

    ipados_top_bar_locator = '//XCUIElementTypeOther[@name="UnifiedBar?isStandaloneBar=true"]/XCUIElementTypeOther[1]'
    ios_mobile_top_bar_locator = (
        '//*[contains(@name, "SafariWindow")]/XCUIElementTypeOther[1]/XCUIElementTypeOther/XCUIElementTypeOther'
    )

    def __init__(self, driver_wrapper: DriverWrapper) -> None:
        """Initialize NativeSafari with elements for native iOS Safari controls."""
        from mops.base.element import Element  # noqa: PLC0415

        self.driver_wrapper = driver_wrapper

        self.custom_top_bar_locator = self.driver_wrapper.caps.get(CUSTOM_TOP_BAR_LOCATOR_CAPABILITY, '')
        self.top_bar = Element(
            Locator(
                mobile=self.custom_top_bar_locator or self.ios_mobile_top_bar_locator,
                tablet=self.custom_top_bar_locator or self.ipados_top_bar_locator,
            ),
            name='safari top bar',
            driver_wrapper=driver_wrapper,
        )

        self.custom_bottom_bar_locator = self.driver_wrapper.caps.get(CUSTOM_BOTTOM_BAR_LOCATOR_CAPABILITY, '')
        self.bottom_bar = Element(
            self.custom_bottom_bar_locator or self.ios_18_bottom_bar_locator,
            name='safari bottom bar',
            driver_wrapper=driver_wrapper,
        )

        self.custom_done_button_locator = self.driver_wrapper.caps.get(CUSTOM_DONE_BUTTON_LOCATOR_CAPABILITY, '')
        self.keyboard_done_button = Element(
            locator=self.custom_done_button_locator or self.ios_keyboard_hide_button,
            name='keyboard Done button',
            driver_wrapper=driver_wrapper,
        )

    def get_bottom_bar_height(self) -> int:
        """
        Get iOS/iPadOS bottom bar height

        :return: int
        """
        if self.driver_wrapper.is_tablet:
            return 0  # iPad does not have bottom bar

        if not self.custom_bottom_bar_locator:
            ios_version = float(self.driver_wrapper.driver.caps.get('platformVersion', 18.2))

            if ios_version >= self._IOS_VERSION_26:
                self.bottom_bar.locator = self.ios_26_bottom_bar_locator
            elif ios_version >= self._IOS_VERSION_18_2:
                self.bottom_bar.locator = self.ios_18_bottom_bar_locator

        return self.bottom_bar.size.height
