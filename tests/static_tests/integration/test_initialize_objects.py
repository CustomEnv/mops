import re

from mops.base.element import Element
from mops.base.group import Group
from mops.exceptions import NotInitializedException


class Section(Group):
    def __int__(self):
        super().__init__('section_test_initialize_objects')
    el = Element('el_test_initialize_objects')


class RootSection(Group):
    def __int__(self):
        super().__init__('section_1_test_initialize_objects')
    section = Section('')


def test_initialize_objects(mocked_selenium_driver):
    """ covers initialize_objects function """
    root_section = RootSection('')
    assert root_section._initialized
    assert root_section.section._initialized
    assert root_section.section.el._initialized
    try:
        RootSection.section.el.element
    except NotInitializedException as exc:
        pattern = r'Element object at .* object is not initialized. Try to initialize base object first or call it directly as a method'
        assert re.search(pattern, exc.msg)
    else:
        raise AssertionError('NotInitializedException should be raised')


def test_initialize_object_manually(mocked_selenium_driver):
    """ covers __call__ of Element """
    assert RootSection.section.el.driver_wrapper is None
    assert RootSection.section.el._initialized == False
    called_object = RootSection.section.el()
    assert called_object.driver_wrapper == mocked_selenium_driver
    assert called_object._initialized == True

