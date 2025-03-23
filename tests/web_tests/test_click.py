import time

import pytest

from mops.exceptions import ElementNotInteractableException
from mops.utils.internal_utils import HALF_WAIT_EL, QUARTER_WAIT_EL


def test_click_and_wait(pizza_order_page, platform):
    pizza_order_page.submit_button.click()
    after_click_displayed = pizza_order_page.error_modal.wait_visibility().is_displayed()
    if 'play' in platform:
        time.sleep(1)
    pizza_order_page.error_modal.click_outside(-1, -10)
    after_click_outside_not_displayed = not pizza_order_page.error_modal.wait_hidden().is_displayed()
    assert all((after_click_displayed, after_click_outside_not_displayed))


def test_click_into_center(mouse_event_page_v2):
    mouse_event_page_v2.mouse_click_card().click_area.click_into_center()
    result_x, result_y = mouse_event_page_v2.mouse_click_card().get_result_coordinates()
    expected_x_range, expected_y_range = mouse_event_page_v2.mouse_click_card().get_click_area_middle()
    assert result_x in expected_x_range, f'result_x: {result_x}; expected_x: {expected_x_range}'
    assert result_y in expected_y_range, f'result_y: {result_y}; expected_y: {expected_y_range}'


@pytest.mark.parametrize('coordinates', [(-2, -2), (2, 2), (2, -2), (-2, 2), (2, 0), (0, 2)])
def test_click_outside(mouse_event_page_v2, coordinates):
    mouse_event_page_v2.mouse_click_card().click_area_parent.click_outside(*coordinates)
    assert not mouse_event_page_v2.mouse_click_card().is_click_proceeded()


@pytest.mark.low
@pytest.mark.skip_platform('playwright', reason='selenium only')
def test_click_on_covered_button_initial(expected_condition_page, caplog):
    assert expected_condition_page.cover_button.is_displayed()

    try:
        expected_condition_page.covered_button.click()
    except ElementNotInteractableException:
        pass
    else:
        raise AssertionError('Unexpected behaviour. Case not covered')


@pytest.mark.low
def test_click_on_covered_button_positive(expected_condition_page, caplog, platform):
    expected_condition_page.set_min_and_max_wait(3, 3)

    expected_condition_page.covered_trigger.click()
    expected_condition_page.covered_button.click()

    if platform == 'selenium':
        assert caplog.messages.count('Caught ElementNotInteractableException, retrying...') >= 2

    assert not expected_condition_page.cover_button.is_displayed()



@pytest.mark.low
@pytest.mark.skip_platform('playwright', reason='selenium only')
def test_click_on_covered_button_negative(expected_condition_page, caplog):
    expected_condition_page.set_min_and_max_wait(20, 20)

    expected_condition_page.covered_trigger.click()

    start = time.time()
    try:  # The retry logic should be equal to 5 seconds from first exception + some time for first execution
        expected_condition_page.covered_button.click()
    except ElementNotInteractableException:
        assert time.time() - start < HALF_WAIT_EL + QUARTER_WAIT_EL
    else:
        raise AssertionError('Unexpected behaviour. Case not covered')
