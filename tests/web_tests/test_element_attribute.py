import pytest


def test_element_attribute_radio_button(forms_page):
    assert forms_page.controls_form.selenium_radio.get_attribute('value') == 'SELENIUM'


def test_element_attribute_checkbox(forms_page):
    assert forms_page.controls_form.python_checkbox.get_attribute('value') == 'PYTHON'


@pytest.mark.low
@pytest.mark.skip_platform('playwright', reason='selenium only case')
def test_get_attribute_dynamic_element(mouse_event_page_v1):
    button = mouse_event_page_v1.jump_button
    for i in range(20):
        text = button.get_attribute('innerText') or button.get_attribute('textContent')
        assert text in ('Container 1', 'Container 2'), f'Actual text: {text}'
