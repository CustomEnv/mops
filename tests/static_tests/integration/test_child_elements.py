from mops.base.element import Element
from mops.base.group import Group


class Section1:
    some_element = None


class Section2(Group, Section1):
    def __init__(self, locator, name):
        super().__init__(locator, name=name)

    some_element = Element('some_element')


class DummySection(Section1):
    pass


class Section3(Section2, DummySection):
    def __init__(self):
        super().__init__('section3', name='section3')

    pass


def test_child_elements(mocked_selenium_driver):
    section2 = Section2('.section2', name='section2')
    section3 = Section3()
    assert section3.some_element
    assert section3.some_element._initialized  # noqa
    assert section3.sub_elements

    assert section2.some_element
    assert section2.some_element._initialized  # noqa
    assert section2.sub_elements
