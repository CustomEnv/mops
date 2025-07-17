from __future__ import annotations

import re
from typing import Any, Union

from selenium.webdriver.common.by import By

from mops.exceptions import InvalidLocatorException
from mops.mixins.objects.locator import Locator
from mops.mixins.objects.locator_type import LocatorType
from mops.utils.internal_utils import all_tags


DEFAULT_MATCH = (f"{LocatorType.XPATH}=", f"{LocatorType.ID}=", f"{LocatorType.CSS}=", f"{LocatorType.TEXT}=")
XPATH_MATCH = ("/", "./", "(/")
CSS_MATCH = ("#", ".")
CSS_REGEXP = r"[#.\[\]=]"
APPIUM_LOCATOR_TYPES = [
    LocatorType.IOS_PREDICATE,
    LocatorType.IOS_UIAUTOMATION,
    LocatorType.IOS_CLASS_CHAIN,
    LocatorType.ANDROID_UIAUTOMATOR,
    LocatorType.ANDROID_VIEWTAG,
    LocatorType.ANDROID_DATA_MATCHER,
    LocatorType.ANDROID_VIEW_MATCHER,
    LocatorType.WINDOWS_UI_AUTOMATION,
    LocatorType.ACCESSIBILITY_ID,
    LocatorType.IMAGE,
    LocatorType.CUSTOM,
]


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
        locator = obj.locator.split(f"{LocatorType.ID}=")[-1]
        obj.locator = f'[{LocatorType.ID}="{locator}"]'
        obj.locator_type = By.CSS_SELECTOR

    # Checking the regular locators

    elif locator.startswith(XPATH_MATCH):
        obj.locator_type = By.XPATH
        obj.log_locator = f'{LocatorType.XPATH}={locator}'

    elif locator.startswith(CSS_MATCH) or re.search(CSS_REGEXP, locator):
        obj.locator_type = By.CSS_SELECTOR
        obj.log_locator = f'{LocatorType.CSS}={locator}'

    elif locator in all_tags or all(tag in all_tags for tag in locator.split()):
        obj.locator_type = By.CSS_SELECTOR
        obj.log_locator = f'{LocatorType.CSS}={locator}'

    elif " " in locator:
        obj.locator = f'//*[contains(text(), "{locator}")]'
        obj.locator_type = By.XPATH
        obj.log_locator = f'{LocatorType.XPATH}={obj.locator}'

    # Default to ID if nothing else matches

    else:
        locator = obj.locator.split(f"{LocatorType.ID}=")[-1]
        obj.locator = f'[{LocatorType.ID}="{locator}"]'
        obj.locator_type = By.CSS_SELECTOR
        obj.log_locator = f'{LocatorType.ID}={locator}'


def set_playwright_locator(obj: Any):
    """
    Sets playwright locator & locator type
    """
    locator = obj.locator.strip()
    obj.log_locator = locator

    # Checking the supported locators

    if locator.startswith(DEFAULT_MATCH):
        obj.locator_type = locator.partition('=')[0]
        return

    # Checking the regular locators

    elif locator.startswith(XPATH_MATCH):
        obj.locator_type = LocatorType.XPATH

    elif locator.startswith(CSS_MATCH) or re.search(CSS_REGEXP, locator):
        obj.locator_type = LocatorType.CSS

    elif locator in all_tags or all(tag in all_tags for tag in locator.split()):
        obj.locator_type = LocatorType.CSS

    elif " " in locator:
        obj.locator_type = LocatorType.TEXT

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

    locator = obj.locator.strip()

    if ':id/' in locator:  # Mobile com.android selector
        obj.locator_type = By.CSS_SELECTOR
        obj.log_locator = f'{LocatorType.ID}={locator}'
    elif '=' in locator and any([f'{locator_type}=' in locator for locator_type in APPIUM_LOCATOR_TYPES]):
        partition = locator.partition('=')
        obj.locator_type = partition[0]
        obj.locator = partition[-1]
        obj.log_locator = locator
