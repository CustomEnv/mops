import pytest

from mops.base.element import Element
from mops.base.group import Group
from mops.base.page import Page
from mops.exceptions import DriverWrapperException

group = Group('some_group', name='test group')
element = Element('some_locator', name='test element')


@pytest.mark.parametrize('obj', [element, group], ids=['element', 'group'])
def test_locator_access_without_driver(obj):
    assert obj.locator


@pytest.mark.parametrize('obj', [element, group], ids=['element', 'group'])
def test_locator_type_access_without_driver(obj):
    assert obj.locator_type is None


@pytest.mark.parametrize('obj', [element, group], ids=['element', 'group'])
def test_log_locator_access_without_driver(obj):
    assert obj.log_locator


def test_page_init_without_driver():
    try:
        Page('some_page', name='test page')
    except DriverWrapperException as exc:
        msg = ('Cannot initialize Page: unsupported driver type "NoneType". '
               'Expected Playwright, Appium or Selenium driver instance')
        assert msg == exc.msg
