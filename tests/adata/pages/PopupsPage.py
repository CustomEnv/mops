from __future__ import annotations

from mops.base.element import Element
from mops.base.group import Group
from mops.base.page import Page
from tests.settings import domain_name, automation_playground_repo_name


class PopupsPage(Page):

    def __init__(self):
        super().__init__('popups-page', name='Popups page')

    url = f'{domain_name}/{automation_playground_repo_name}/multi_window.html'

    open_popup_button = Element('#open-popup-button', name='open popup button')

    def open_popup(self) -> OverlayPopup:
        self.open_popup_button.scroll_into_view(sleep=0.5).click()
        return OverlayPopup().wait_visibility()

class OverlayPopup(Group):
    def __init__(self):
        super().__init__('overlay-popup', name='overlay-popup')

    popup_text = Element('popup-text', name='popup text')
