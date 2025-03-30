from mops.base.element import Element
from mops.base.group import Group
from mops.base.page import Page
from mops.mixins.objects.locator import Locator
from tests.settings import domain_name, automation_playground_repo_name


class ExpectedConditionPage(Page):
    def __init__(self):
        self.url = f'{domain_name}/{automation_playground_repo_name}/expected_conditions.html'
        self.value_card = WaitValueCard()
        self.wait_visibility_card = WaitVisibilityCard()
        self.wait_hidden_card = WaitHiddenCard()
        self.blinking_card = BlinkingCard()
        self.frame_card = WaitFrameCard()
        self.test_driver = self.driver_wrapper
        super().__init__('//*[contains(@class, "card") and contains(., "wait")]', name='Expected condition page')
        self.test_driver = self.driver_wrapper

    min_wait_input = Element('min_wait', name='min wait input')
    max_wait_input = Element('max_wait', name='max wait input')

    alert_trigger = Element('alert_trigger', name='alert trigger')
    prompt_trigger = Element('prompt_trigger', name='prompt trigger')

    covered_trigger = Element('covered_trigger', name='covered button trigger')
    cover_button = Element('cover', name='cover button')
    covered_button = Element('covered_button', name='covered button')

    alert_handled_badge = Element('alert_handled_badge', name='alert handled badge')
    confirm_badge = Element('confirm_ok_badge', name='confirm badge')
    canceled_badge = Element('confirm_cancelled_badge', name='cancelled badge')

    alert_ok_button = Element(Locator('', ios='//XCUIElementTypeStaticText[@name="OK"]'), name='accept alert button')
    alert_cancel_button = Element(Locator('', ios='//XCUIElementTypeStaticText[@name="Cancel"]'), name='cancel alert button')

    def set_min_and_max_wait(self, min_wait=1, max_wait=1):
        self.min_wait_input.set_text(str(min_wait))
        self.max_wait_input.set_text(str(max_wait))
        return self


class WaitValueCard(Group):
    def __init__(self):
        super().__init__('//*[contains(@class, "card") and contains(., "Wait for text")]', name='value card group')

    wait_for_text_button = Element('wait_for_text', name='wait for text button')
    wait_for_value_input = Element('wait_for_value', name='wait for value input')
    trigger_button = Element('text_value_trigger', name='trigger wait button')


class WaitVisibilityCard(Group):
    def __init__(self):
        super().__init__('//*[contains(@class, "card") and contains(., "Wait for element to be visible")]',
                         name='element visible card')

    trigger_button = Element('visibility_trigger', name='trigger button')
    target_button = Element('visibility_target', name='target button')


class WaitHiddenCard(Group):
    def __init__(self):
        super().__init__('//*[contains(@class, "card") and contains(., "Wait for element to be Invisible")]',
                         name='element hidden card')

    trigger_button = Element('invisibility_trigger', name='trigger button')
    target_spinner = Element('invisibility_target', name='target spinner')


class BlinkingCard(Group):
    def __init__(self):
        super().__init__('//*[contains(@class, "card") and contains(., "Wait for blinking panel")]',
                         name='blinking card')

    interval_input = Element('interval-input', name='interval input')
    interval_button = Element('interval-button', name='interval button')
    blinking_panel = Element('blinking-panel', name='blinking panel')

    def set_interval(self):
        self.interval_input.set_text('400')
        self.interval_button.click()


class WaitFrameCard(Group):
    def __init__(self):
        super().__init__('//*[contains(@class, "card") and contains(., "Wait for frame to be available")]',
                         name='element card')

    trigger_button = Element('wait_for_frame', name='trigger button')
    frame = Element('iframe', name='target iframe')


class WaitValueCardBroken(Group):
    def __init__(self):
        super().__init__('.card', name='value card broken selector')

    trigger_button = Element('text_value_trigger', name='trigger wait button1')
    any_row = Element('.row', name='any row')
