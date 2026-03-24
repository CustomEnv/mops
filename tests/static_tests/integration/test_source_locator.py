import pytest

from mops.base.element import Element
from mops.base.group import Group
from mops.mixins.objects.locator import Locator
from tests.static_tests.conftest import desktop_drivers, desktop_ids, mobile_drivers, mobile_ids


xpath_locator = '//div[@class="test"]'
css_locator = '.test-class'
id_locator = 'test-id'
ios_locator = 'ios_locator'
android_locator = 'android_locator'
mobile_locator = 'mobile_locator'

multi_platform_locator = Locator(
    default='default_locator',
    desktop='desktop_locator',
    mobile=mobile_locator,
    ios=ios_locator,
    android=android_locator,
)


class SourceLocatorGroup(Group):
    def __init__(self):
        super().__init__(xpath_locator, name='source locator group')

    sub_element = Element(css_locator, name='sub element')
    multi_element = Element(multi_platform_locator, name='multi element')


@pytest.mark.parametrize('driver', desktop_drivers, ids=desktop_ids)
def test_source_locator_preserved_for_string_xpath(driver, request):
    request.getfixturevalue(driver)
    element = Element(xpath_locator, name='xpath element')
    assert element.source_locator == xpath_locator


@pytest.mark.parametrize('driver', desktop_drivers, ids=desktop_ids)
def test_source_locator_preserved_for_string_css(driver, request):
    request.getfixturevalue(driver)
    element = Element(css_locator, name='css element')
    assert element.source_locator == css_locator


@pytest.mark.parametrize('driver', desktop_drivers, ids=desktop_ids)
def test_source_locator_preserved_for_string_id(driver, request):
    request.getfixturevalue(driver)
    element = Element(id_locator, name='id element')
    assert element.source_locator == id_locator


@pytest.mark.parametrize('driver', desktop_drivers, ids=desktop_ids)
def test_source_locator_differs_from_transformed_locator(driver, request):
    request.getfixturevalue(driver)
    element = Element(xpath_locator, name='xpath element')
    assert element.source_locator == xpath_locator
    assert element.locator != xpath_locator or element.source_locator == element.locator


@pytest.mark.parametrize('driver', desktop_drivers, ids=desktop_ids)
def test_source_locator_preserved_for_locator_dataclass(driver, request):
    request.getfixturevalue(driver)
    element = Element(multi_platform_locator, name='multi element')
    assert element.source_locator is multi_platform_locator


@pytest.mark.parametrize('driver', mobile_drivers, ids=mobile_ids)
def test_source_locator_preserved_for_locator_dataclass_mobile(driver, request):
    request.getfixturevalue(driver)
    element = Element(multi_platform_locator, name='multi element')
    assert element.source_locator is multi_platform_locator
    assert isinstance(element.locator, str)


@pytest.mark.parametrize('driver', desktop_drivers, ids=desktop_ids)
def test_source_locator_preserved_in_sub_elements(driver, request):
    request.getfixturevalue(driver)
    group = SourceLocatorGroup()
    assert group.source_locator == xpath_locator
    assert group.sub_element.source_locator == css_locator
    assert group.multi_element.source_locator is multi_platform_locator
