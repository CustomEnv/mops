from __future__ import annotations

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


def generate_locator(web_element: object, driver: object) -> str:
    """Generate a stable XPath locator from a live Selenium WebElement.

    Tries stable attributes in priority order, falls back to positional XPath.
    The returned locator uses the ``xpath=`` prefix used by MOPS.
    """
    try:
        attrs: dict[str, str] = {}
        tag: str = web_element.tag_name

        for attr_name in ('id', *_TEST_ATTRS, 'name', 'aria-label', 'placeholder', 'type', 'role', 'href', 'class'):
            val = web_element.get_attribute(attr_name)
            if val:
                attrs[attr_name] = val.strip()

        text = (web_element.text or '').strip()
    except Exception:
        return _positional_xpath(web_element, driver)

    # id (unique by spec)
    el_id = attrs.get('id', '')
    if el_id and ' ' not in el_id:
        return f'xpath=//*[@id="{el_id}"]'

    # data-* test attributes
    for test_attr in _TEST_ATTRS:
        val = attrs.get(test_attr, '')
        if val:
            return f'xpath=//*[@{test_attr}="{val}"]'

    # name
    name = attrs.get('name', '')
    if name:
        return f'xpath=//{tag}[@name="{name}"]'

    # aria-label
    aria = attrs.get('aria-label', '')
    if aria:
        escaped = aria.replace('"', '\\"')
        return f'xpath=//*[@aria-label="{escaped}"]'

    # visible text (short, single-line)
    if text and len(text) <= 50 and '\n' not in text:
        escaped = text.replace('"', '\\"')
        return f'xpath=//{tag}[normalize-space(.)="{escaped}"]'

    # type + tag
    el_type = attrs.get('type', '')
    if el_type:
        return f'xpath=//{tag}[@type="{el_type}"]'

    # stable class (filter out dynamic-looking tokens)
    cls = attrs.get('class', '')
    if cls:
        stable = [c for c in cls.split() if not any(c.lower().startswith(p) for p in _DYNAMIC_CLASS_PREFIXES)]
        if stable:
            return f'xpath=//{tag}[contains(@class, "{stable[0]}")]'

    return _positional_xpath(web_element, driver)


def _positional_xpath(web_element: object, driver: object) -> str:
    try:
        path: str = driver.execute_script(_GET_POSITIONAL_XPATH_JS, web_element)
        return f'xpath={path}'
    except Exception:
        return f'xpath=//{web_element.tag_name}'
