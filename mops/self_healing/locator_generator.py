from __future__ import annotations

import re
from typing import TYPE_CHECKING

from selenium.common.exceptions import WebDriverException

from mops.self_healing.healer import _HTML_DEFAULT_ATTRS

if TYPE_CHECKING:
    from collections.abc import Callable

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

#: Attributes that are checked on the element (in order) for locator generation.
_LOOKED_UP_ATTRS = (
    'id',
    'data-testid',
    'data-test',
    'data-cy',
    'data-qa',
    'data-automation-id',
    'name',
    'aria-label',
    'placeholder',
    'type',
    'role',
    'href',
    'class',
)

#: Test-id attributes checked first, in order of preference.
_TEST_ATTRS = ('data-testid', 'data-test', 'data-cy', 'data-qa', 'data-automation-id')

_MAX_TEXT_LENGTH = 50
_MAX_CLASS_TOKENS = 2

# Build-time generated values. These change on every frontend rebuild, so any
# locator built from them is guaranteed to break on the next deploy.
_HASH_SUFFIX_RE = re.compile(r'#\w{1,12}$')
_REACT_ID_RE = re.compile(r'^:r[0-9a-z]+:$')
_ANGULAR_SCOPE_RE = re.compile(r'^_ng(content|host)-')
_ALNUM_ONLY_RE = re.compile(r'[A-Za-z0-9]+')
_HAS_DIGIT_RE = re.compile(r'\d')
_HAS_UPPER_RE = re.compile(r'[A-Z]')
_CAMEL_CASE_RE = re.compile(r'^[a-z]+([A-Z][a-z0-9]*)+$')
_AMBIGUOUS_SHORT_LENGTH = 8
_MIN_HASH_LENGTH = 12


def _xpath_literal(value: str) -> str:
    """Build a valid XPath 1.0 string literal for *value*.

    XPath has no backslash escapes, so a value containing both quote kinds must
    be assembled with ``concat()``.
    """
    if '"' not in value:
        return f'"{value}"'
    if "'" not in value:
        return f"'{value}'"
    parts = ", '\"', ".join(f'"{part}"' for part in value.split('"'))
    return f'concat({parts})'


def _is_generated_value(value: str) -> bool:
    """Detect values generated at build/run time (hashes, React/Angular ids).

    Such values look stable in a single session but change on the next frontend
    build, so a locator built from them is broken by design.
    """
    if not value:
        return True
    if _HASH_SUFFIX_RE.search(value) or _REACT_ID_RE.match(value) or _ANGULAR_SCOPE_RE.match(value):
        return True

    # Short mixed-case blobs ('Tep', 'Uip', 'MdO') — neither all-lowercase nor camelCase.
    if (
        len(value) <= _AMBIGUOUS_SHORT_LENGTH
        and _ALNUM_ONLY_RE.fullmatch(value)
        and _HAS_UPPER_RE.search(value)
        and not _CAMEL_CASE_RE.match(value)
    ):
        return True

    # Long alphanumeric blobs with digits ('a1b2c3d4e5f6g7') are hashes too.
    return (
        len(value) >= _MIN_HASH_LENGTH
        and _ALNUM_ONLY_RE.fullmatch(value) is not None
        and _HAS_DIGIT_RE.search(value) is not None
    )


def _stable_class_tokens(class_value: str) -> list[str]:
    """Return class tokens that are safe to use in a locator.

    Drops build-time hash suffixes (``some-element#Tep`` → ``some-element``),
    state/JS helper classes and generated-looking tokens.
    """
    tokens: list[str] = []
    for raw_token in (class_value or '').split():
        token = _HASH_SUFFIX_RE.sub('', raw_token).strip()
        if not token:
            continue
        if any(token.lower().startswith(prefix) for prefix in _DYNAMIC_CLASS_PREFIXES):
            continue
        if token in tokens:
            continue
        tokens.append(token)
    return tokens


def _build_providers(tag: str, attrs: dict[str, str], text: str) -> list[str]:
    """Build ordered ``xpath=`` locator candidates from extracted element data.

    Ordered by stability: id → test ids → name → aria-label → name+type →
    type → class → text → (caller appends the positional XPath).
    """
    providers: list[str] = []

    def add(provider: str) -> None:
        if provider not in providers:
            providers.append(provider)

    # id (unique by spec) — but only when it is not generated at build time
    element_id = attrs.get('id', '')
    if element_id and ' ' not in element_id and not _is_generated_value(element_id):
        add(f'xpath=//*[@id={_xpath_literal(element_id)}]')

    # data-* test attributes
    for test_attr in _TEST_ATTRS:
        value = attrs.get(test_attr, '')
        if value:
            add(f'xpath=//*[@{test_attr}={_xpath_literal(value)}]')

    # name
    name = attrs.get('name', '')
    if name:
        add(f'xpath=//{tag}[@name={_xpath_literal(name)}]')

    # aria-label
    aria_label = attrs.get('aria-label', '')
    if aria_label:
        add(f'xpath=//*[@aria-label={_xpath_literal(aria_label)}]')

    # name + type — more specific than either attribute alone
    element_type = attrs.get('type', '')
    if name and element_type:
        add(f'xpath=//{tag}[@name={_xpath_literal(name)} and @type={_xpath_literal(element_type)}]')

    # type + tag
    if element_type:
        add(f'xpath=//{tag}[@type={_xpath_literal(element_type)}]')

    # class — only stable tokens, combined with "and" when several are present
    class_tokens = _stable_class_tokens(attrs.get('class', ''))[:_MAX_CLASS_TOKENS]
    if class_tokens:
        conditions = ' and '.join(f'contains(@class, {_xpath_literal(token)})' for token in class_tokens)
        add(f'xpath=//{tag}[{conditions}]')

    # visible text (short, single-line)
    if text and len(text) <= _MAX_TEXT_LENGTH and '\n' not in text:
        add(f'xpath=//{tag}[normalize-space(.)={_xpath_literal(text)}]')

    return providers


def generate_locator(web_element: object, driver: object) -> list[str]:
    """Generate all stable XPath locators from a live Selenium WebElement.

    Returns locators ordered by preference (most stable first); the caller tries
    each until one is verified. Each locator uses the ``xpath=`` prefix used by MOPS.
    """
    try:
        tag = web_element.tag_name
        attrs = _extract_attrs(web_element.get_attribute, driver, web_element, tag)
        text = (web_element.text or '').strip()
    except WebDriverException:
        return [_positional_xpath(web_element, driver)]

    return [*_build_providers(tag, attrs, text), _positional_xpath(web_element, driver)]


def generate_locator_pw(locator_element: object, driver_wrapper: object) -> list[str]:
    """Generate all stable XPath locators from a live Playwright Locator.

    Same ordering and rules as :func:`generate_locator`, using Playwright's
    Locator API (:meth:`get_attribute`, :meth:`evaluate`) instead of Selenium's
    WebElement API.
    """
    try:
        tag: str = locator_element.evaluate('el => el.tagName.toLowerCase()')
        attrs = _extract_attrs(
            locator_element.get_attribute,
            driver_wrapper,
            locator_element,
            tag,
            has_attribute=lambda name: locator_element.evaluate(f'el => el.hasAttribute("{name}")'),
        )
        text = (locator_element.evaluate('el => (el.textContent || "").trim()') or '').strip()
    except Exception:  # noqa: BLE001
        return [_positional_xpath_pw(locator_element, driver_wrapper)]

    return [*_build_providers(tag, attrs, text), _positional_xpath_pw(locator_element, driver_wrapper)]


def _extract_attrs(
    get_attribute: Callable[[str], str | None],
    driver: object,
    element: object,
    tag: str,
    has_attribute: Callable[[str], bool] | None = None,
) -> dict[str, str]:
    """Collect locator-relevant attributes, dropping HTML defaults that are absent from the DOM.

    ``get_attribute()`` reports HTML defaults (e.g. ``text`` for ``<input>``,
    ``submit`` for ``<button>``) even when the attribute is not in the markup —
    an XPath built from such a phantom attribute would never match.
    """
    if has_attribute is None:
        has_attribute = lambda name: bool(  # noqa: E731
            driver.execute_script(f'return arguments[0].hasAttribute("{name}")', element)
        )

    attrs: dict[str, str] = {}
    for attr_name in _LOOKED_UP_ATTRS:
        if attr_name in _HTML_DEFAULT_ATTRS.get(tag, {}) and not has_attribute(attr_name):
            continue
        value = get_attribute(attr_name)
        if value:
            attrs[attr_name] = value.strip()
    return attrs


def _positional_xpath(web_element: object, driver: object) -> str:
    try:
        path: str = driver.execute_script(_GET_POSITIONAL_XPATH_JS, web_element)
    except WebDriverException:
        return f'xpath=//{web_element.tag_name}'
    else:
        return f'xpath={path}'


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
