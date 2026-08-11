from __future__ import annotations

from unittest.mock import MagicMock

from mops.self_healing.locator_generator import generate_locator, generate_locator_pw


def _selenium_element(attrs: dict, has_attr: bool, tag: str = 'input'):
    """Build a fake Selenium WebElement with get_attribute and text mocks."""
    web_element = MagicMock()
    web_element.tag_name = tag
    web_element.get_attribute.side_effect = lambda a: attrs.get(a)
    web_element.text = ''
    driver = MagicMock()
    # first execute_script call: hasAttribute('type'); second: positional xpath
    driver.execute_script.side_effect = [has_attr, f'/html[1]/body[1]/{tag}[1]']
    return web_element, driver


def test_generate_locator_skips_default_type():
    """An <input> without a physical type attribute must not get a @type XPath."""
    web_element, driver = _selenium_element(attrs={'class': 'my-input'}, has_attr=False)

    locators = generate_locator(web_element, driver)

    assert not any('@type' in loc for loc in locators)
    assert any('contains(@class, "my-input")' in loc for loc in locators)


def test_generate_locator_uses_physical_type():
    """An <input> with a real type attribute keeps the @type XPath candidate."""
    web_element, driver = _selenium_element(attrs={'type': 'checkbox', 'name': 'agree'}, has_attr=True)

    locators = generate_locator(web_element, driver)

    assert any('@type="checkbox"' in loc for loc in locators)
    assert any('@name="agree"' in loc for loc in locators)


def test_generate_locator_skips_default_button_type():
    """A <button> without a physical type must not get a @type="submit" XPath."""
    web_element, driver = _selenium_element(attrs={'class': 'btn'}, has_attr=False, tag='button')

    locators = generate_locator(web_element, driver)

    assert not any('@type' in loc for loc in locators)
    assert any('contains(@class, "btn")' in loc for loc in locators)


def _pw_element(attrs: dict, has_attr: bool, tag: str = 'input'):
    """Build a fake Playwright Locator with evaluate/get_attribute mocks."""
    locator_element = MagicMock()
    # evaluate order: tag -> hasAttribute('type') -> textContent
    locator_element.evaluate.side_effect = [tag, has_attr, '']
    locator_element.get_attribute.side_effect = lambda a: attrs.get(a)
    driver_wrapper = MagicMock()
    driver_wrapper.execute_script.return_value = f'/html[1]/body[1]/{tag}[1]'
    return locator_element, driver_wrapper


def test_generate_locator_pw_skips_default_type():
    """Playwright: no @type XPath when type is not physically present."""
    locator_element, driver_wrapper = _pw_element(attrs={'class': 'my-input'}, has_attr=False)

    locators = generate_locator_pw(locator_element, driver_wrapper)

    assert not any('@type' in loc for loc in locators)
    assert any('contains(@class, "my-input")' in loc for loc in locators)


def test_generate_locator_pw_uses_physical_type():
    """Playwright: keeps @type XPath when type is physically present."""
    locator_element, driver_wrapper = _pw_element(attrs={'type': 'checkbox', 'name': 'agree'}, has_attr=True)

    locators = generate_locator_pw(locator_element, driver_wrapper)

    assert any('@type="checkbox"' in loc for loc in locators)
    assert any('@name="agree"' in loc for loc in locators)
