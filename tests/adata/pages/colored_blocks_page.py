from __future__ import annotations

from typing import List

from mops.base.element import Element
from mops.base.group import Group
from mops.base.page import Page
from tests.settings import domain_name, automation_playground_repo_name


class Row(Group):
    def __init__(self, locator, name: str):
        self.card = Element('.card', name=f'any colored block of {name}')
        super().__init__(locator, name=name)


class ColoredBlocksPage(Page):
    
    def __init__(self):
        super().__init__('colored-blocks-page', name='Colored blocks page')

    url = f'{domain_name}/{automation_playground_repo_name}/colored_blocks.html'

    blocks_container = Element('.container', name='colored blocks container')
    row1 = Row('row-1', name='first blocks row')
    row2 = Row('row-2', name='second blocks row')
    card = Element('.card', name='any colored block')
    navbar = Element('.navbar', name='navbar')
    open_popup_button = Element('#open-popup-button', name='open popup button')

    def get_all_cards(self) -> List[Element]:
        return self.card.wait_elements_count(16).all_elements

    def open_popup(self) -> OverlayPopup:
        self.open_popup_button.scroll_into_view().click()
        return OverlayPopup().wait_visibility()

class OverlayPopup(Group):
    def __init__(self):
        super().__init__('#overlay-popup', name='overlay-popup')

    popup_text = Element('#popup-text', name='popup text')