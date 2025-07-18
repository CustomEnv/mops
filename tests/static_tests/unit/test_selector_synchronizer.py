from types import SimpleNamespace

import pytest
from mops.mixins.objects.locator_type import LocatorType

from mops.utils.selector_synchronizer import set_selenium_selector, set_playwright_locator, set_appium_selector
from selenium.webdriver.common.by import By


@pytest.mark.parametrize('method', (set_selenium_selector, set_appium_selector), ids=['selenium', 'appium'])
@pytest.mark.parametrize(
    "locator_input, expected_locator, expected_locator_type, expected_log_locator",
    [
        ("xpath=//div", "//div", LocatorType.XPATH, "xpath=//div"),
        ("text=Hello", '//*[contains(text(), "Hello")]', LocatorType.XPATH, "text=Hello"),
        ("css=.class", ".class", By.CSS_SELECTOR, "css=.class"),
        ("id=my_id", '[id="my_id"]', By.CSS_SELECTOR, "id=my_id"),
        ("/html/body/div", "/html/body/div", LocatorType.XPATH, "xpath=/html/body/div"),
        ("#my_element", "#my_element", By.CSS_SELECTOR, "css=#my_element"),
        ("button", "button", By.CSS_SELECTOR, "css=button"),
        ("tbody tr td span", "tbody tr td span", By.CSS_SELECTOR, "css=tbody tr td span"),
        ("textarea", "textarea", By.CSS_SELECTOR, "css=textarea"),
        ("[href='/some/url']", "[href='/some/url']", By.CSS_SELECTOR, "css=[href='/some/url']"),
    ],
)
def test_set_selenium_selector(locator_input, expected_locator, expected_locator_type, expected_log_locator, method):
    mock_obj = SimpleNamespace()
    mock_obj.locator = locator_input
    method(mock_obj)
    assert expected_locator == mock_obj.locator
    assert expected_locator_type == mock_obj.locator_type
    assert expected_log_locator == mock_obj.log_locator


@pytest.mark.parametrize(
    "locator_input, expected_locator",
    [
        ("xpath=//div", "xpath=//div"),
        ("text=Hello", "text=Hello"),
        ("css=.class", "css=.class"),
        ("id=my_id", "id=my_id"),
        ("/html/body/div", "xpath=/html/body/div"),
        ("#my_element", "css=#my_element"),
        ("button", "css=button"),
        ("tbody tr td span", "css=tbody tr td span"),
        ("[href='/some/url']", "css=[href='/some/url']"),
    ],
)
def test_set_playwright_locator(locator_input, expected_locator):
    mock_obj = SimpleNamespace()
    mock_obj.locator = locator_input
    set_playwright_locator(mock_obj)
    assert expected_locator == mock_obj.locator
    assert expected_locator == mock_obj.log_locator
    assert expected_locator.partition('=')[0] == mock_obj.locator_type


@pytest.mark.parametrize(
    "locator, locator_type",
    [
        ("type == 'XCUIElementTypeButton' AND name CONTAINS 'Submit'", '-ios predicate string'),
        (".elements()[0].elements()[1]", '-ios uiautomation'),
        ("**/XCUIElementTypeCell[`name == 'Settings'`]", '-ios class chain'),
        ('new UiSelector().text("Login")', '-android uiautomator'),
        ("my_custom_tag", '-android viewtag'),
        ('{"name"="hasEntry", "args"=["KEY", "VALUE"]}', '-android datamatcher'),
        ('{"name"="withText", "args"=["Continue"]}', '-android viewmatcher'),
        ("Name='OK' AND ControlType='Button'", '-windows uiautomation'),
        ("login_button", 'accessibility id'),
        ("/path/to/image.png", '-image'),
        ('{"selector"="myCustomSelector", "strategy"="myCustomStrategy"}', '-custom'),
    ],
)
def test_set_appium_selector(locator, locator_type):
    mock_obj = SimpleNamespace()
    log_locator = f'{locator_type}={locator}'
    mock_obj.locator =log_locator
    set_appium_selector(mock_obj)
    assert locator == mock_obj.locator
    assert locator_type == mock_obj.locator_type
    assert log_locator == mock_obj.log_locator
