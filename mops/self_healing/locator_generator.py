from __future__ import annotations

from selenium.common.exceptions import WebDriverException

from mops.self_healing.healer import _HTML_DEFAULT_ATTRS

_GET_POSITIONAL_XPATH_JS = """
return (function(el) {
    var parts = [];
    while (el && el.nodeType === 1) {
        var idx = 1;
        var sib = el.previousSibling;
        while (sib) {
            if (sib.nodeType === 1 && sib.tagName === el.tagName) idx++;
            sib = sib.previousSibling;
        }
        parts.unshift(el.tagName.toLowerCase() + '[' + idx + ']');
        el = el.parentNode;
    }
    return '/' + parts.join('/');
})(arguments[0]);
"""

_DYNAMIC_CLASS_PREFIXES = ('js-', 'is-', 'has-', 'active', 'disabled', 'selected', 'open', 'closed')

_TEST_ATTRS = ('data-testid', 'data-test', 'data-cy', 'data-qa', 'data-automation-id')

_MAX_TEXT_LENGTH = 50


def generate_locator(web_element: object, driver: object) -> list[str]:  # noqa: PLR0912
    """Generate all possible stable XPath locators from a live Selenium WebElement.

    Returns locators ordered by preference (most stable first).
    The caller should try each in order until one succeeds.
    Each locator uses the ``xpath=`` prefix used by MOPS.
    """
    try:
        attrs: dict[str, str] = {}
        tag: str = web_element.tag_name

        for attr_name in ('id', *_TEST_ATTRS, 'name', 'aria-label', 'placeholder', 'type', 'role', 'href', 'class'):
            # get_attribute() reports HTML defaults (e.g. 'text' for <input>,
            # 'submit' for <button>) even when the attribute is absent — that
            # would yield an XPath that never matches. Skip phantom attributes
            # that have an HTML default for this tag unless physically present.
            if attr_name in _HTML_DEFAULT_ATTRS.get(tag, {}) and not driver.execute_script(
                f'return arguments[0].hasAttribute("{attr_name}")', web_element
            ):
                continue
            val = web_element.get_attribute(attr_name)
            if val:
                attrs[attr_name] = val.strip()

        text = (web_element.text or '').strip()
    except WebDriverException:
        return [_positional_xpath(web_element, driver)]

    providers: list[str] = []

    # id (unique by spec)
    el_id = attrs.get('id', '')
    if el_id and ' ' not in el_id:
        providers.append(f'xpath=//*[@id="{el_id}"]')

    # data-* test attributes
    for test_attr in _TEST_ATTRS:
        val = attrs.get(test_attr, '')
        if val:
            providers.append(f'xpath=//*[@{test_attr}="{val}"]')

    # name
    name = attrs.get('name', '')
    if name:
        providers.append(f'xpath=//{tag}[@name="{name}"]')

    # aria-label
    aria = attrs.get('aria-label', '')
    if aria:
        escaped = aria.replace('"', '\\"')
        providers.append(f'xpath=//*[@aria-label="{escaped}"]')

    # type + tag
    el_type = attrs.get('type', '')
    if el_type:
        providers.append(f'xpath=//{tag}[@type="{el_type}"]')

    # stable class (filter out dynamic-looking tokens)
    cls = attrs.get('class', '')
    if cls:
        stable = [c for c in cls.split() if not any(c.lower().startswith(p) for p in _DYNAMIC_CLASS_PREFIXES)]
        if stable:
            providers.append(f'xpath=//{tag}[contains(@class, "{stable[0]}")]')

    # visible text (short, single-line)
    if text and len(text) <= _MAX_TEXT_LENGTH and '\n' not in text:
        escaped = text.replace('"', '\\"')
        providers.append(f'xpath=//{tag}[normalize-space(.)="{escaped}"]')

    providers.append(_positional_xpath(web_element, driver))
    return providers


def _positional_xpath(web_element: object, driver: object) -> str:
    try:
        path: str = driver.execute_script(_GET_POSITIONAL_XPATH_JS, web_element)
    except WebDriverException:
        return f'xpath=//{web_element.tag_name}'
    else:
        return f'xpath={path}'


def generate_locator_pw(locator_element: object, driver_wrapper: object) -> list[str]:  # noqa: PLR0912
    """Generate all possible stable XPath locators from a live Playwright Locator.

    Returns locators ordered by preference (most stable first).
    The caller should try each in order until one succeeds.
    Each locator uses the ``xpath=`` prefix used by MOPS.

    Uses Playwright's Locator API (:meth:`get_attribute`, :meth:`evaluate`)
    instead of Selenium's WebElement API.
    """
    try:
        tag: str = locator_element.evaluate('el => el.tagName.toLowerCase()')

        attrs: dict[str, str] = {}
        for attr_name in ('id', *_TEST_ATTRS, 'name', 'aria-label', 'placeholder', 'type', 'role', 'href', 'class'):
            # get_attribute() may report HTML defaults even when the attribute is
            # absent from the DOM — skip phantom attributes (those with an HTML
            # default for this tag) unless physically present.
            if attr_name in _HTML_DEFAULT_ATTRS.get(tag, {}) and not locator_element.evaluate(
                f'el => el.hasAttribute("{attr_name}")'
            ):
                continue
            val = locator_element.get_attribute(attr_name)
            if val:
                attrs[attr_name] = val.strip()

        text = (locator_element.evaluate('el => (el.textContent || "").trim()') or '').strip()
    except Exception:  # noqa: BLE001
        return [_positional_xpath_pw(locator_element, driver_wrapper)]

    providers: list[str] = []

    # id (unique by spec)
    el_id = attrs.get('id', '')
    if el_id and ' ' not in el_id:
        providers.append(f'xpath=//*[@id="{el_id}"]')

    # data-* test attributes
    for test_attr in _TEST_ATTRS:
        val = attrs.get(test_attr, '')
        if val:
            providers.append(f'xpath=//*[@{test_attr}="{val}"]')

    # name
    name = attrs.get('name', '')
    if name:
        providers.append(f'xpath=//{tag}[@name="{name}"]')

    # aria-label
    aria = attrs.get('aria-label', '')
    if aria:
        escaped = aria.replace('"', '\\"')
        providers.append(f'xpath=//*[@aria-label="{escaped}"]')

    # type + tag
    el_type = attrs.get('type', '')
    if el_type:
        providers.append(f'xpath=//{tag}[@type="{el_type}"]')

    # stable class (filter out dynamic-looking tokens)
    cls = attrs.get('class', '')
    if cls:
        stable = [c for c in cls.split() if not any(c.lower().startswith(p) for p in _DYNAMIC_CLASS_PREFIXES)]
        if stable:
            providers.append(f'xpath=//{tag}[contains(@class, "{stable[0]}")]')

    # visible text (short, single-line)
    if text and len(text) <= _MAX_TEXT_LENGTH and '\n' not in text:
        escaped = text.replace('"', '\\"')
        providers.append(f'xpath=//{tag}[normalize-space(.)="{escaped}"]')

    providers.append(_positional_xpath_pw(locator_element, driver_wrapper))
    return providers


def _positional_xpath_pw(locator_element: object, driver_wrapper: object) -> str:
    try:
        path: str = driver_wrapper.execute_script(_GET_POSITIONAL_XPATH_JS, locator_element)
    except Exception:  # noqa: BLE001
        try:
            tag = locator_element.evaluate('el => el.tagName.toLowerCase()')
        except Exception:  # noqa: BLE001
            tag = '*'
        return f'xpath=//{tag}'
    else:
        return f'xpath={path}'
