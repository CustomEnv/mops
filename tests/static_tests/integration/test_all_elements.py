from mock.mock import MagicMock

from mops.base.element import Element
from mops.base.group import Group


class Card(Group):
    def __init__(self, driver_wrapper=None):
        super().__init__('.card', name='card', driver_wrapper=driver_wrapper)
        self.any_button = Element('a', name='any button')

    button = Element('a', name='button')


def test_all_elements_inside_all_elements(mocked_selenium_driver):
    """all_elements when parent of Element is Group with instance-level sub-element (static analog)"""
    mock_sources = [MagicMock(), MagicMock(), MagicMock()]
    all_cards = Card()._get_all_elements(mock_sources)

    for card in all_cards:
        assert 'any_button' in card.sub_elements, 'instance-level any_button must be in sub_elements'
        assert card.any_button.parent is card

        mock_button_sources = [MagicMock(), MagicMock()]
        buttons = card.any_button._get_all_elements(mock_button_sources)
        for button in buttons:
            assert button.parent is not None


def test_all_elements_init_sub_element_isolated(mocked_selenium_driver):
    """Each wrapped card must have its own independent any_button instance"""
    mock_sources = [MagicMock(), MagicMock(), MagicMock()]
    all_cards = Card()._get_all_elements(mock_sources)

    for i, card_a in enumerate(all_cards):
        for j, card_b in enumerate(all_cards):
            if i != j:
                assert card_a.any_button is not card_b.any_button


def test_all_elements_class_sub_element_has_parent(mocked_selenium_driver):
    """Class-level button must also have correct parent on each wrapped card"""
    mock_sources = [MagicMock(), MagicMock()]
    all_cards = Card()._get_all_elements(mock_sources)

    for card in all_cards:
        assert card.button.parent is card
