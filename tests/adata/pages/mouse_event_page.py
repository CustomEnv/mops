from __future__ import annotations

from mops.base.driver_wrapper import DriverWrapper
from mops.base.element import Element
from mops.base.group import Group
from mops.base.page import Page
from tests.settings import domain_name, automation_playground_repo_name


class MouseEventPageMixin:

    choose_language_button = Element('button.dropbtn', name='"Choose language" button', wait=True)
    dropdown = Element('div.dropdown-content', name='dropdown with languages')
    header_logo = Element('[class = "navbar-brand abs"]', name='header logo', wait=True)

    def button_with_text(self, text):
        return Element(f'//button[contains(.,"{text}")]', name=f'button with text: {text}')

    def mouse_click_card(self):
        return MouseClickCard()

    def drag_n_drop(self):
        return DragAndDrop()

class MouseEventPageV1(Page, MouseEventPageMixin):
    url = f'{domain_name}/{automation_playground_repo_name}/mouse_events.html'

    def __init__(self, driver_wrapper: DriverWrapper = None):
        super().__init__('//h2[.="Mouse Click Actions"]', name='Mouse events page V1', driver_wrapper=driver_wrapper)

    jump_button = Element('jump-button', name='jumping button')


class MouseEventPageV2(Page, MouseEventPageMixin):
    url = f'{domain_name}/{automation_playground_repo_name}/mouse_events_v2.html'

    def __init__(self, driver_wrapper: DriverWrapper = None):
        super().__init__('//h2[.="Mouse Click Actions"]', name='Mouse events page V2', driver_wrapper=driver_wrapper)


class MouseEventPageWithUnexpectedWait(MouseEventPageV2):
    dropdown = Element('div.dropdown-content', name='dropdown with languages and wait', wait=True)


class DragAndDrop(Group):
    def __init__(self):
        super().__init__('//*[contains(@class, "card") and .//.="Drag and Drop"]', name='drag and drop card')

    card_body = Element('.card-body', name='card body')
    drag_target = Element('drop_target', name='drag target button', parent=card_body)


class MouseClickCard(Group):
    def __init__(self):
        super().__init__('//*[contains(@class, "card") and .//.="Mouse Click Actions"]', name='mouse click card')

    click_area = Element('click_area', name='click area')
    click_area_parent = Element('//*[@id="click_area"]/..', name='click area')
    x_result = Element('click_x', name='x result')
    y_result = Element('click_y', name='y result')

    drag_source = Element('drag_source', name='drag source button')  # Wrong one

    @property
    def any_button(self):
        return Element('button', name='any button')

    @property
    def any_button_without_parent(self):
        return Element('button', name='any button wo parent', parent=False)

    @property
    def any_button_with_custom_parent(self):
        return Element('button', name='any button custom parent', parent=self.y_result)

    def get_result_coordinates(self):
        return [int(element.wait_for_text().text.split(' ')[1]) for element in (self.x_result, self.y_result)]

    def get_click_area_middle(self):
        el_rect = self.click_area.get_rect()
        height, width = int(el_rect['height'] / 2), int(el_rect['width'] / 2)
        return [range(side - 2, side + 2) for side in [width, height]]

    def is_click_proceeded(self):
        return self.x_result.is_displayed() or self.y_result.is_displayed()

    def click_area_func(self):
        return self.click_area

    def drag_source_func(self):
        return self.drag_source  # Wrong one
