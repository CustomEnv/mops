

def test_element_attribute_radio_button(forms_page):
    assert forms_page.controls_form.selenium_radio.get_attribute('value') == 'SELENIUM'


def test_element_attribute_checkbox(forms_page):
    assert forms_page.controls_form.python_checkbox.get_attribute('value') == 'PYTHON'


def test_get_attribute_dynamic_element(mouse_event_page_v1):
    for i in range(20):
        assert mouse_event_page_v1.jump_button.get_attribute('innerText') in ('Container 1', 'Container 2')
