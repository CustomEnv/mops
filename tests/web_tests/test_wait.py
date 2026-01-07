import pytest

from mops.exceptions import ContinuousWaitException, TimeoutException


@pytest.mark.low
def test_get_rect_dynamic_element(mouse_event_page_v1):
    for i in range(20):
        assert all(mouse_event_page_v1.jump_button.get_rect().values())
        assert mouse_event_page_v1.jump_button.location
        assert mouse_event_page_v1.jump_button.size


def test_wait_elements_count_v1(forms_page):
    forms_page.validation_form.form_mixin.input.type_text('sample')
    forms_page.validation_form.submit_form_button.click()
    forms_page.validation_form.any_error.wait_elements_count(expected_count=4)
    assert forms_page.validation_form.any_error.get_elements_count() == 4


def test_wait_elements_count_v2(expected_condition_page):
    initial_count = expected_condition_page.frame_card.frame.get_elements_count()
    expected_condition_page.frame_card.trigger_button.click()
    target_count = expected_condition_page.frame_card.frame.wait_elements_count(1).get_elements_count()
    assert all((initial_count == 0, target_count == 1))


@pytest.mark.xfail(reason='TODO: Implementation')
def test_wait_element_stop_changing(progressbar_page):
    # bar = progressbar_page.progress_bar.element
    # progressbar_page.start_button.click()
    # locations_list = [tuple(bar.size.values()) for _ in range(200) if not time.sleep(0.1)]
    pass


@pytest.mark.xfail(reason='TODO: Implementation')
def test_wait_element_stop_moving(progressbar_page):
    # bar = progressbar_page.progress_bar.element
    # progressbar_page.start_button.click()
    # locations_list = [tuple(bar.location.values()) for _ in range(200) if not time.sleep(0.1)]
    pass


# Wait cases


def test_wait_hidden_positive(expected_condition_page, caplog):
    assert not expected_condition_page.wait_hidden_card.target_spinner.is_hidden()
    expected_condition_page.wait_hidden_card.trigger_button.click()
    expected_condition_page.wait_hidden_card.target_spinner.wait_hidden()
    assert 'Wait until "target spinner" becomes hidden' in str(caplog.messages)
    assert expected_condition_page.wait_hidden_card.target_spinner.is_hidden()


def test_wait_visibility_positive(expected_condition_page, caplog):
    assert not expected_condition_page.wait_visibility_card.target_button.is_displayed()
    expected_condition_page.wait_visibility_card.trigger_button.click()
    expected_condition_page.wait_visibility_card.target_button.wait_visibility()
    assert 'Wait until "target button" becomes visible' in str(caplog.messages)
    assert expected_condition_page.wait_visibility_card.target_button.is_displayed()


def test_wait_hidden_negative(expected_condition_page, caplog):
    assert not expected_condition_page.wait_hidden_card.target_spinner.is_hidden()
    try:
        expected_condition_page.wait_hidden_card.target_spinner.wait_hidden(timeout=0.5)
    except TimeoutException as exc:
        assert ('"target spinner" still visible after 0.5 seconds. Selector=\'xpath=//*[contains(@class, "card") and'
                ' contains(., "Wait for element to be Invisible")] >> id=invisibility_target\'.') in exc.msg
    else:
        raise Exception('Unexpected behaviour. Case not covered')


def test_wait_visibility_negative(expected_condition_page, caplog):
    assert not expected_condition_page.wait_visibility_card.target_button.is_displayed()
    try:
        expected_condition_page.wait_visibility_card.target_button.wait_visibility(timeout=0.5)
    except TimeoutException as exc:
        assert ('"target button" not visible after 0.5 seconds. Selector=\'xpath=//*[contains(@class, "card") and'
                ' contains(., "Wait for element to be visible")] >> id=visibility_target\'.') in exc.msg
    else:
        raise Exception('Unexpected behaviour. Case not covered')


# Continuous wait cases


def test_wait_continuous_hidden_positive(expected_condition_page, caplog):
    assert not expected_condition_page.wait_hidden_card.target_spinner.is_hidden()
    expected_condition_page.wait_hidden_card.trigger_button.click()
    expected_condition_page.wait_hidden_card.target_spinner.wait_hidden(continuous=1)
    assert 'Starting continuous "wait_hidden" for the "target spinner" for next 1 seconds' in str(caplog.messages)
    assert expected_condition_page.wait_hidden_card.target_spinner.is_hidden()


def test_wait_continuous_visibility_positive(expected_condition_page, caplog):
    assert not expected_condition_page.wait_visibility_card.target_button.is_displayed()
    expected_condition_page.wait_visibility_card.trigger_button.click()
    expected_condition_page.wait_visibility_card.target_button.wait_visibility(continuous=1)
    assert 'Starting continuous "wait_visibility" for the "target button" for next 1 seconds' in str(caplog.messages)
    assert expected_condition_page.wait_visibility_card.target_button.is_displayed()


def test_wait_continuous_hidden_negative(expected_condition_page, caplog):
    expected_condition_page.blinking_card.set_interval()
    try:
        expected_condition_page.blinking_card.blinking_panel.wait_hidden(continuous=True)
    except ContinuousWaitException as exc:
        assert 'The continuous "wait_hidden" of the "blinking panel" is no met after 0.' in exc.msg
    else:
        raise Exception('Unexpected behaviour. Case not covered')


def test_wait_continuous_visibility_negative(expected_condition_page, caplog):
    expected_condition_page.blinking_card.set_interval()
    try:
        expected_condition_page.blinking_card.blinking_panel.wait_visibility(continuous=True)
    except ContinuousWaitException as exc:
        assert 'The continuous "wait_visibility" of the "blinking panel" is no met after 0.' in exc.msg
    else:
        raise Exception('Unexpected behaviour. Case not covered')
