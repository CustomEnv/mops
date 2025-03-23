import contextlib
import random

import pytest

from mops.base.element import Element
from tests.adata.pages.expected_condition_page import WaitValueCardBroken
from mops.exceptions import InvalidSelectorException
from tests.adata.pages.keyboard_page import KeyboardPage


@pytest.mark.skip_platform(
    'playwright',
    reason='Playwright handle these cases and does not throw some Exceptions in such cases'
)
def test_multiple_parents_found_positive(expected_condition_page):
    """ There should not be any exception if element found even there are multiple parents for him """
    WaitValueCardBroken().any_row._get_element(wait=False)


def test_element_displayed_positive(base_playground_page):
    assert base_playground_page.kube.is_displayed()


def test_element_displayed_negative(base_playground_page):
    assert not base_playground_page.kube_broken.is_displayed()


def test_all_elements_count_positive(base_playground_page):
    assert base_playground_page.any_link.get_elements_count() > 1


def test_all_elements_count_negative(base_playground_page):
    assert base_playground_page.kube_broken.get_elements_count() == 0


@pytest.mark.xfail_platform('android', 'ios', reason='Can not get text from that element. TODO: Rework test')
def test_type_clear_text_get_value(pizza_order_page):
    text_to_send = str(random.randint(100, 9999))
    pizza_order_page.quantity_input.type_text(text_to_send)
    text_added = pizza_order_page.quantity_input.value == text_to_send
    pizza_order_page.quantity_input.clear_text()
    text_erased = pizza_order_page.quantity_input.value == ''
    assert all((text_added, text_erased))


@pytest.mark.xfail_platform('selenium-safari', reason='Fail in CI env')
def test_hover(mouse_event_page_v2):
    initial_not_displayed = not mouse_event_page_v2.dropdown.is_displayed()
    mouse_event_page_v2.choose_language_button.scroll_into_view(sleep=0.1).hover()
    after_hover_displayed = mouse_event_page_v2.dropdown.wait_visibility_without_error().is_displayed()
    mouse_event_page_v2.choose_language_button.hover_outside()
    after_outside_hover_displayed = not mouse_event_page_v2.dropdown.wait_hidden().is_displayed()
    assert all((initial_not_displayed, after_hover_displayed, after_outside_hover_displayed))


@pytest.mark.low
def test_wait_for_text_dynamic_element(mouse_event_page_v1):
    """ Case: 102034539 """
    for i in range(20):
        assert mouse_event_page_v1.jump_button.wait_for_text(timeout=1)

@pytest.mark.low
def test_get_text_dynamic_element(mouse_event_page_v1):
    """ Case: 89391107 """
    for i in range(20):
        assert mouse_event_page_v1.jump_button.text in ('Container 1', 'Container 2')


# Cases when parent is another element


def test_parent_element_positive(base_playground_page):
    assert base_playground_page.kube_parent.is_displayed()


def test_parent_element_negative(base_playground_page):
    assert not base_playground_page.kube_wrong_parent.is_displayed()


def test_parent_element_wait_visible_positive(base_playground_page):
    assert base_playground_page.kube_parent.wait_visibility()


def test_parent_element_wait_hidden_negative(base_playground_page):
    assert base_playground_page.kube_wrong_parent.wait_hidden()


# All elements


def test_all_elements_with_parent(base_playground_page):
    """ all_elements when parent of Element is other element """
    all_elements = base_playground_page.any_div_with_parent.all_elements
    assert all_elements, 'did not find elements on page'

    for element in all_elements:
        assert element.parent.locator == base_playground_page.any_section.locator


def test_element_group_all_elements_child(second_playground_page):
    """ all_elements when parent of Element is Group """
    all_cards = second_playground_page.get_all_cards()

    for index, element_object in enumerate(all_cards):
        if 0 < index < len(all_cards) - 1:
            assert id(element_object.button) != id(all_cards[index - 1].button)
            assert element_object.button.element != all_cards[index - 1].button.element
            assert element_object.button.element != all_cards[index + 1].button.element

    all_cards[1].button.click()
    assert KeyboardPage().wait_page_loaded().is_page_opened()


def test_all_elements_recursion(base_playground_page):
    try:
        base_playground_page.kube.all_elements[0].all_elements
    except RecursionError:
        pass
    else:
        raise AssertionError('RecursionError was not raised')\


def test_element_execute_script(forms_page, driver_wrapper):
    new_text = 'driver wrapper automation'
    forms_page.controls_form.german_slider.execute_script('arguments[0].textContent = arguments[1];', new_text)
    assert forms_page.controls_form.german_slider.text == new_text

def test_element_locator_check(mouse_event_page_v2, driver_wrapper):
    # Let's keep Elements here, for encapsulation purposes
    # Reformat test if any trouble occur
    locators = (
        '.card.text-center',
        '[class *= card][class *= text-center]',
        '#footer',
        '[href*="https://www.linkedin.com/in"]'
    )
    invalid_prefixes = ('xpath', 'text', 'id')

    for locator in locators:
        assert Element(locator).is_displayed()
        assert Element(f'css={locator}').is_displayed()
        for invalid_prefix in invalid_prefixes:
            with contextlib.suppress(InvalidSelectorException):
                assert not Element(f'{invalid_prefix}={locator}').is_displayed()

    locators = ('//*[contains(@class, "card")]', '//body/div')
    invalid_prefixes = ('css', 'text', 'id')
    for locator in locators:
        assert Element(locator).is_displayed()
        assert Element(f'xpath={locator}').is_displayed()
        for invalid_prefix in invalid_prefixes:
            with contextlib.suppress(InvalidSelectorException):
                assert not Element(f'{invalid_prefix}={locator}').is_displayed()

    locators = ('drop_target', 'drag_source')
    invalid_prefixes = ('css', 'xpath', 'text')
    for locator in locators:
        assert Element(locator).is_displayed()
        assert Element(f'id={locator}').is_displayed()

        for invalid_prefix in invalid_prefixes:
            with contextlib.suppress(InvalidSelectorException):
                assert not Element(f'{invalid_prefix}={locator}').is_displayed()

    choose_lang_button_name = 'Choose Language'
    locators = (choose_lang_button_name, )
    invalid_prefixes = ('css', 'xpath', 'id')
    for locator in locators:
        assert Element(locator).is_displayed()
        assert Element(f'text={locator}').is_displayed()
        # if locator == choose_lang_button_name:  # TODO: Move to separate test
        #     assert not Element('.dropdown-content').is_displayed()
        #     Element(locator).scroll_into_view().click()
        #     Element('.dropdown-content').wait_visibility()

        for invalid_prefix in invalid_prefixes:
            with contextlib.suppress(InvalidSelectorException):
                assert not Element(f'{invalid_prefix}={locator}').is_displayed()
