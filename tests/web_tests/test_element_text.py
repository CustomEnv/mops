import pytest


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

@pytest.mark.xfail_platform('android', 'ios', reason='Can not get value from that element. TODO: Rework test')
def test_wait_element_value(expected_condition_page):
    expected_condition_page.value_card.trigger_button.click()
    value_without_wait = expected_condition_page.value_card.wait_for_value_input.value
    expected_condition_page.value_card.wait_for_value_input.wait_for_value()
    value_with_wait = expected_condition_page.value_card.wait_for_value_input.value == 'Dennis Ritchie'
    assert all((not value_without_wait, value_with_wait))


def test_wait_element_text(expected_condition_page, driver_wrapper):
    btn = expected_condition_page.value_card.wait_for_text_button

    expected_condition_page.value_card.trigger_button.click()
    value_without_wait = btn.text
    assert not value_without_wait
    assert btn.wait_for_text().text == 'Submit'


def test_wait_empty_element_text(expected_condition_page, driver_wrapper):
    btn = expected_condition_page.value_card.wait_for_text_button
    assert btn.wait_for_text('').text == ''


def test_wait_empty_element_value(expected_condition_page):
    btn = expected_condition_page.value_card.wait_for_value_input
    assert btn.wait_for_value('').value == ''
