from tests.adata.pages.mouse_event_page import MouseEventPageV2


def test_group_with_class_var_positive(mouse_event_page_v2):
    mouse_click_card = MouseEventPageV2().mouse_click_card()
    assert mouse_click_card.click_area.is_displayed()


def test_group_with_class_var_negative(mouse_event_page_v2):
    mouse_click_card = MouseEventPageV2().mouse_click_card()
    assert not mouse_click_card.drag_source.is_displayed()


def test_group_with_class_func_positive(mouse_event_page_v2):
    mouse_click_card = MouseEventPageV2().mouse_click_card()
    assert mouse_click_card.click_area_func().is_displayed()


def test_group_with_class_func_negative(mouse_event_page_v2):
    mouse_click_card = MouseEventPageV2().mouse_click_card()
    assert not mouse_click_card.drag_source_func().is_displayed()


def test_group_without_init(forms_page):
    assert forms_page.validation_form.form_mixin.input.parent.parent

    forms_page.validation_form.form_mixin.input.type_text('sample')
    forms_page.validation_form.submit_form_button.click()

    assert not forms_page.validation_form.invalid_city_error.is_displayed()
    assert forms_page.validation_form.invalid_feedback_error.is_displayed()
    assert forms_page.validation_form.invalid_zip_error.is_displayed()
    assert forms_page.validation_form.invalid_terms_error.is_displayed()
