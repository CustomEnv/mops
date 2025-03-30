from mops.mixins.objects.locator import Locator


class NativeContext:

    def __init__(self, driver_wrapper):
        self.driver_wrapper = driver_wrapper

    def __enter__(self):
        self.driver_wrapper.switch_to_native()

    def __exit__(self, *args):
        self.driver_wrapper.switch_to_web()


class NativeSafari:

    ios_keyboard_hide_button = "//XCUIElementTypeButton[@name='Done']"
    ios_mobile_small_bottom_bar_locator = '//*[@name="CapsuleViewController"]/XCUIElementTypeOther[1]'
    ios_mobile_large_bottom_bar_locator = f'{ios_mobile_small_bottom_bar_locator}/XCUIElementTypeOther[1]' \
                                          f'/XCUIElementTypeOther[2]'
    ios_tablet_top_bar_locator = '//XCUIElementTypeOther[@name="UnifiedBar?isStandaloneBar=true"]' \
                                 '/XCUIElementTypeOther[1]'
    ios_mobile_top_bar_locator = '//*[contains(@name, "SafariWindow")]/XCUIElementTypeOther[1]' \
                                 '/XCUIElementTypeOther/XCUIElementTypeOther'

    def __init__(self, driver_wrapper):
        from mops.base.element import Element
        self.driver_wrapper = driver_wrapper

        self.top_bar = Element(
            Locator(mobile=self.ios_mobile_top_bar_locator, tablet=self.ios_tablet_top_bar_locator),
            name='safari top bar',
            driver_wrapper=driver_wrapper,
        )

        self.bottom_bar = Element(self.ios_mobile_small_bottom_bar_locator, name='safari bottom bar',
                                  driver_wrapper=driver_wrapper)
        self.keyboard_done_button = Element(locator=self.ios_keyboard_hide_button, name='keyboard Done button',
                                            driver_wrapper=driver_wrapper)

    def get_bottom_bar_height(self) -> int:
        """
        Get iOS/iPadOS bottom bar height.

        :return: int
        """
        if self.driver_wrapper.is_tablet:
            return 0  # iPad does not have bottom bar

        bottom_bar_height = self.bottom_bar.size.height
        if bottom_bar_height > 350:  # Large devices have different locator
            self.bottom_bar.locator = self.ios_mobile_large_bottom_bar_locator
            bottom_bar_height = self.bottom_bar.size.height

        return bottom_bar_height
