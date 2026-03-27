from dataclasses import dataclass


@dataclass
class Locator:
    """Represents a WEB UI element locator with platform-specific variations."""

    default: str | None = None
    """
    All: The default locator for the object, used by default if no other locators are specified
     or if no specific platform/device type is detected.
    """

    desktop: str | None = None
    """
    All: The locator for desktop environments, typically used for browsers on desktop platforms.
    """

    mobile: str | None = None
    """
    All: The locator for general mobile environments, used for mobile platforms other than iOS and Android,
     as well as for mobile resolutions of desktop browsers.
    """

    tablet: str | None = None
    """
    Appium only: The locator specifically for tablet devices, useful for web and app automation on tablets.
    The "is_tablet: True" desired_capability is required.
    """

    ios: str | None = None
    """
    Appium only: The locator specifically for iOS devices,
     allowing for targeting locators specific to iOS applications.
    """

    android: str | None = None
    """
    Appium only: The locator specifically for Android devices,
     allowing for targeting locators specific to Android applications.
    """
