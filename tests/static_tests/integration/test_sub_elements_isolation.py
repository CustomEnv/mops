from mops.base.element import Element
from mops.base.group import Group
from mops.base.page import Page


class BaseRow(Group):
    name_cell = Element('css=.name', name='name_cell')
    status_cell = Element('css=.status', name='status_cell')


class RowA(BaseRow):
    extra_a = Element('css=.extra-a', name='extra_a')


class RowB(BaseRow):
    extra_b = Element('css=.extra-b', name='extra_b')


class TableA(Group):
    row = RowA('css=tr.a', name='rowA')


class TableB(Group):
    row = RowB('css=tr.b', name='rowB')


# -- Class level --

class PageClassLevel(Page):
    table_a = TableA('css=.tbl-a', name='tableA')
    table_b = TableB('css=.tbl-b', name='tableB')


# -- Init level --

class PageInitLevel(Page):
    def __init__(self):
        self.table_a = TableA('css=.tbl-a', name='tableA')
        self.table_b = TableB('css=.tbl-b', name='tableB')
        super().__init__('body', name='PageInitLevel')


def test_class_level_sub_elements_not_leaking(mocked_selenium_driver):
    """Sub elements of nested groups should not leak to parent level (class level)"""
    page = PageClassLevel()
    assert list(page.table_a.sub_elements.keys()) == ['row']
    assert list(page.table_b.sub_elements.keys()) == ['row']


def test_init_level_sub_elements_not_leaking(mocked_selenium_driver):
    """Sub elements of nested groups should not leak to parent level (__init__ level)"""
    page = PageInitLevel()
    assert list(page.table_a.sub_elements.keys()) == ['row']
    assert list(page.table_b.sub_elements.keys()) == ['row']


def test_class_level_correct_row_types(mocked_selenium_driver):
    """Nested groups should preserve their correct types (class level)"""
    page = PageClassLevel()
    assert isinstance(page.table_a.row, RowA)
    assert isinstance(page.table_b.row, RowB)


def test_init_level_correct_row_types(mocked_selenium_driver):
    """Nested groups should preserve their correct types (__init__ level)"""
    page = PageInitLevel()
    assert isinstance(page.table_a.row, RowA)
    assert isinstance(page.table_b.row, RowB)


def test_class_level_row_sub_elements(mocked_selenium_driver):
    """Row sub elements should contain only own and inherited elements (class level)"""
    page = PageClassLevel()
    assert 'name_cell' in page.table_a.row.sub_elements
    assert 'status_cell' in page.table_a.row.sub_elements
    assert 'extra_a' in page.table_a.row.sub_elements
    assert 'extra_b' not in page.table_a.row.sub_elements

    assert 'name_cell' in page.table_b.row.sub_elements
    assert 'status_cell' in page.table_b.row.sub_elements
    assert 'extra_b' in page.table_b.row.sub_elements
    assert 'extra_a' not in page.table_b.row.sub_elements


def test_init_level_row_sub_elements(mocked_selenium_driver):
    """Row sub elements should contain only own and inherited elements (__init__ level)"""
    page = PageInitLevel()
    assert 'name_cell' in page.table_a.row.sub_elements
    assert 'status_cell' in page.table_a.row.sub_elements
    assert 'extra_a' in page.table_a.row.sub_elements
    assert 'extra_b' not in page.table_a.row.sub_elements

    assert 'name_cell' in page.table_b.row.sub_elements
    assert 'status_cell' in page.table_b.row.sub_elements
    assert 'extra_b' in page.table_b.row.sub_elements
    assert 'extra_a' not in page.table_b.row.sub_elements


def test_class_level_no_cross_contamination(mocked_selenium_driver):
    """Elements from one table's row should not appear on another table (class level)"""
    page = PageClassLevel()
    assert not hasattr(page.table_a, 'extra_b')
    assert not hasattr(page.table_b, 'extra_a')


def test_init_level_no_cross_contamination(mocked_selenium_driver):
    """Elements from one table's row should not appear on another table (__init__ level)"""
    page = PageInitLevel()
    assert not hasattr(page.table_a, 'extra_b')
    assert not hasattr(page.table_b, 'extra_a')
