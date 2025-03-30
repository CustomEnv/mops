from __future__ import annotations

from typing import List


from mops.base.element import Element
from mops.base.group import Group
from mops.base.page import Page
from tests.adata.pages.expected_condition_page import ExpectedConditionPage
from tests.adata.pages.keyboard_page import KeyboardPage
from tests.settings import domain_name, automation_playground_repo_name


class PlaygroundMainPage(Page):

    def __init__(self):
        self.url = "http://uitestingplayground.com/home"

        self.any_section = Element('section', name='any section')
        self.any_div_with_parent = Element('div', name='any div inside page locator', parent=self.any_section)
        super().__init__('//*[contains(@class, "container") and .//.="UI Test AutomationPlayground"]',
                         name='Playground main page')

    description_section = Element('description', name='description section')
    overview_section = Element('overview', name='overview section')
    overview_section_broken = Element('overviewshka', name='broken overview section')
    kube = Element('.img-fluid', name='rubik\'s cube')
    any_link = Element('a', name='any link')
    kube_broken = Element('.img-fluid .not-available', name='rubik\'s cube broken locator')
    kube_parent = Element('.img-fluid', name='kube with parent', parent=description_section)
    kube_wrong_parent = Element('.img-fluid', name='kube with wrong parent', parent=overview_section)
    kube_broken_parent = Element('.img-fluid', name='kube with broken parent', parent=overview_section_broken)
    inner_text_1 = Element('//*[@class="row"][2]//*[@class="col-sm"][2]', name='text block 1 for removal')
    inner_text_2 = Element('//*[@class="row"][3]//*[@class="col-sm"][3]', name='text block 2 for removal')
    text_container = Element('#overview .container', name='container of text')
    

class SecondPlaygroundMainPage(Page):
    def __init__(self, driver_wrapper=None):
        self.url = f'{domain_name}/{automation_playground_repo_name}'
        self.dw = driver_wrapper
        super().__init__('//h1[.="The Playground"]', name='Second playground main page', driver_wrapper=driver_wrapper)

    row_with_cards = Element('.row', name='row with cards')

    def get_all_cards(self) -> List[Card]:
        return Card(self.dw).all_elements

    def navigate_to_expected_condition_page(self):
        self.get_all_cards()[0].button.click()
        return ExpectedConditionPage()

    def navigate_to_keyboard_page(self):
        self.get_all_cards()[1].button.click()
        return KeyboardPage()


class Card(Group):
    def __init__(self, driver_wrapper=None):
        super().__init__('.card', name='action cards', driver_wrapper=driver_wrapper)

    button = Element('a', name='proceed card button')
