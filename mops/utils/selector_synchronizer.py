from __future__ import annotations

import re
from typing import Any, Union

from selenium.webdriver.common.by import By

from mops.exceptions import InvalidLocatorException
from mops.mixins.objects.locator import Locator
from mops.mixins.objects.locator_type import LocatorType
from mops.utils.internal_utils import all_tags


_XPATH_MATCH = ("/", "./", "(/")
_CSS_MATCH = ("#", ".")
_CSS_REGEXP = r"[#.\[\]=]"

_DEFAULT_MATCH = (
    f"{LocatorType.XPATH}=",
    f"{LocatorType.ID}=",
    f"{LocatorType.CSS}=",
    f"{LocatorType.TEXT}=",
)

_APPIUM_MATCH = (
    f"{LocatorType.XPATH}=",
    f"{LocatorType.ID}=",
    f"[{LocatorType.ID}=",
    f"{LocatorType.CSS}=",
    f"{LocatorType.TEXT}="
)

_APPIUM_LOCATOR_TYPES = (
    f'{LocatorType.IOS_PREDICATE}=',
    f'{LocatorType.IOS_UIAUTOMATION}=',
    f'{LocatorType.IOS_CLASS_CHAIN}=',
    f'{LocatorType.ANDROID_UIAUTOMATOR}=',
    f'{LocatorType.ANDROID_VIEWTAG}=',
    f'{LocatorType.ANDROID_DATA_MATCHER}=',
    f'{LocatorType.ANDROID_VIEW_MATCHER}=',
    f'{LocatorType.WINDOWS_UI_AUTOMATION}=',
    f'{LocatorType.ACCESSIBILITY_ID}=',
    f'{LocatorType.IMAGE}=',
    f'{LocatorType.CUSTOM}=',
)

_SELENIUM_MOPS_LOCATOR_TYPES = {
    By.ID: LocatorType.ID,
    By.XPATH: LocatorType.XPATH,
    By.CSS_SELECTOR: LocatorType.CSS,
}


def _set_selenium_compatibility_id_locator(obj: Any, split: bool = True) -> Any:
    locator = obj.locator.split(f"{LocatorType.ID}=")[-1] if split else obj.locator

    obj.locator = f'[{LocatorType.ID}="{locator}"]'
    obj.locator_type = By.CSS_SELECTOR
    obj.log_locator = f'{LocatorType.ID}={locator}'


def get_platform_locator(obj: Any):
    """
    Get locator for current platform from object

    :param obj: Page/Group/Element
    :return: current platform locator
    """
    locator: Union[Locator, str] = obj.locator

    if type(locator) is str or not obj.driver_wrapper:
        return locator

    mobile_fallback_locator = locator.mobile or locator.default

    if obj.driver_wrapper.is_desktop:
        locator = locator.desktop or locator.default
    if obj.driver_wrapper.is_tablet:
        locator = locator.tablet or locator.default
    elif obj.driver_wrapper.is_android:
        locator = locator.android or mobile_fallback_locator
    elif obj.driver_wrapper.is_ios:
        locator = locator.ios or mobile_fallback_locator
    elif obj.driver_wrapper.is_mobile:
        locator = mobile_fallback_locator

    if not isinstance(locator, str):
        raise InvalidLocatorException(f'Cannot extract locator for current platform for following object: {obj}')

    return locator


def set_selenium_selector(obj: Any):
    """
    Sets selenium locator & locator type
    """
    locator = obj.locator.strip()
    obj.log_locator = locator

    # Checking the supported locators

    if locator.startswith(f"{LocatorType.XPATH}="):
        obj.locator = obj.locator.split(f"{LocatorType.XPATH}=")[-1]
        obj.locator_type = By.XPATH

    elif locator.startswith(f"{LocatorType.TEXT}="):
        locator = obj.locator.split(f"{LocatorType.TEXT}=")[-1]
        obj.locator = f'//*[contains(text(), "{locator}")]'
        obj.locator_type = By.XPATH

    elif locator.startswith(f"{LocatorType.CSS}="):
        obj.locator = obj.locator.split(f"{LocatorType.CSS}=")[-1]
        obj.locator_type = By.CSS_SELECTOR

    elif locator.startswith(f"{LocatorType.ID}="):
        _set_selenium_compatibility_id_locator(obj)

    # Checking the regular locators

    elif locator.startswith(_XPATH_MATCH):
        obj.locator_type = By.XPATH
        obj.log_locator = f'{LocatorType.XPATH}={locator}'

    elif locator.startswith(_CSS_MATCH) or re.search(_CSS_REGEXP, locator):
        obj.locator_type = By.CSS_SELECTOR
        obj.log_locator = f'{LocatorType.CSS}={locator}'

    elif locator in all_tags or all(tag in all_tags for tag in locator.split()):
        obj.locator_type = By.CSS_SELECTOR
        obj.log_locator = f'{LocatorType.CSS}={locator}'

    # Default to ID if nothing else matches

    else:
        _set_selenium_compatibility_id_locator(obj, split=False)


def set_playwright_locator(obj: Any):
    """
    Sets playwright locator & locator type
    """
    locator: str = obj.locator.strip()

    obj.log_locator = locator

    # Checking the supported locators

    if locator.startswith(_DEFAULT_MATCH):
        obj.locator_type = locator.partition('=')[0]
        return

    # Checking the regular locators

    elif locator.startswith(_XPATH_MATCH):
        obj.locator_type = LocatorType.XPATH

    elif locator.startswith(_CSS_MATCH) or re.search(_CSS_REGEXP, locator):
        obj.locator_type = LocatorType.CSS

    elif locator in all_tags or all(tag in all_tags for tag in locator.split()):
        obj.locator_type = LocatorType.CSS

    # Default to ID if nothing else matches

    else:
        obj.locator_type = LocatorType.ID

    obj.locator = f'{obj.locator_type}={locator}'
    obj.log_locator = obj.locator


def set_appium_selector(obj: Any):
    """
    Sets appium locator & locator type
    """
    set_selenium_selector(obj)

    locator: str = obj.locator.strip()

    # Mobile com.android selector
    if ':id/' in locator and not locator.startswith(_APPIUM_MATCH):
        _set_selenium_compatibility_id_locator(obj)
    elif locator.startswith(_APPIUM_LOCATOR_TYPES):
        partition = locator.partition('=')
        obj.locator_type = partition[0]
        obj.locator = partition[-1]
        obj.log_locator = locator
