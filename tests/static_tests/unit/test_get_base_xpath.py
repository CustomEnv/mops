import pytest

from mops.base.element import Element
from mops.base.group import Group


class ParentGroup(Group):
    def __init__(self):
        super().__init__('//div[@id="parent"]')

    absolute_xpath_child = Element('//span[@class="target"]')
    relative_xpath_child = Element('.//span[@class="target"]')
    css_child = Element('#target')
    parenthesized_xpath_child = Element('(//div)[1]//span')


@pytest.fixture
def group(mocked_play_driver):
    return ParentGroup()


def test_absolute_xpath_bypasses_parent_scoping(group):
    """Absolute XPath locator should resolve from page root, not from parent subtree."""
    child = group.absolute_xpath_child
    base = child._get_base()
    assert base == child.driver, (
        f"Expected page-level driver for absolute XPath, got {type(base)}"
    )


def test_relative_xpath_scoped_to_parent(group):
    """Relative XPath locator should chain through parent element."""
    child = group.relative_xpath_child
    base = child._get_base()
    assert base != child.driver, (
        "Expected parent Locator for relative XPath, got page-level driver"
    )


def test_css_locator_scoped_to_parent(group):
    """CSS locator should chain through parent element."""
    child = group.css_child
    base = child._get_base()
    assert base != child.driver, (
        "Expected parent Locator for CSS selector, got page-level driver"
    )


def test_parenthesized_xpath_scoped_to_parent(group):
    """Parenthesized XPath like (//div)[1]//span should chain through parent."""
    child = group.parenthesized_xpath_child
    base = child._get_base()
    assert base != child.driver, (
        "Expected parent Locator for parenthesized XPath, got page-level driver"
    )


def test_absolute_xpath_without_parent(mocked_play_driver):
    """Standalone element with absolute XPath should return driver regardless."""
    el = Element('//div[@id="solo"]', parent=False)
    base = el._get_base()
    assert base == el.driver


def test_element_without_parent_returns_driver(mocked_play_driver):
    """Element with no parent always returns driver, regardless of locator type."""
    el = Element('.some-class', parent=False)
    base = el._get_base()
    assert base == el.driver
