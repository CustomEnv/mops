# Checkbox tests


def test_checkbox_check(forms_page):
    initial_not_checked = not forms_page.controls_form.python_checkbox.is_checked()
    forms_page.controls_form.python_checkbox.check()
    after_check_checked = forms_page.controls_form.python_checkbox.is_checked()
    assert all((initial_not_checked, after_check_checked))


def test_checkbox_uncheck(forms_page):
    forms_page.controls_form.python_checkbox.check()
    after_check_checked = forms_page.controls_form.python_checkbox.is_checked()
    forms_page.controls_form.python_checkbox.uncheck()
    after_uncheck_not_checked = not forms_page.controls_form.python_checkbox.is_checked()
    assert all((after_check_checked, after_uncheck_not_checked))


# Radiobutton tests


def test_radio_check(forms_page):
    initial_not_checked = not forms_page.controls_form.selenium_radio.is_checked()
    forms_page.controls_form.selenium_radio.check()
    after_check_checked = forms_page.controls_form.selenium_radio.is_checked()
    assert all((initial_not_checked, after_check_checked))


def test_radio_uncheck(forms_page):
    forms_page.controls_form.selenium_radio.check()
    after_check_checked = forms_page.controls_form.selenium_radio.is_checked()
    forms_page.controls_form.protractor_radio.check()
    after_uncheck_not_checked = not forms_page.controls_form.selenium_radio.is_checked()
    assert all((after_check_checked, after_uncheck_not_checked))
