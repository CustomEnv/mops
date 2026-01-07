import pytest

from mops.base.element import Element
from mops.exceptions import *
from mops.mixins.objects.size import Size
from tests.adata.pages.expected_condition_page import ExpectedConditionPage

timeout = 0.1


@pytest.mark.medium
def test_wait_elements_count_error_msg(forms_page):
    forms_page.validation_form.form_mixin.input.type_text('sample')
    forms_page.validation_form.submit_form_button.click()
    try:
        forms_page.validation_form.any_error.wait_elements_count(3, timeout=timeout)
    except UnexpectedElementsCountException as exc:
        assert exc.msg == f'Unexpected elements count of "any error" after {timeout} seconds. ' \
                          f'Actual: 4; Expected: 3.'
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_size_error_msg(forms_page):
    try:
        forms_page.validation_form.wait_for_size(Size(200, 400), timeout=timeout)
    except UnexpectedElementSizeException as exc:
        assert f'Unexpected size for "Validation form" after {timeout} seconds. ' in exc.msg
        assert 'Actual: Size' in exc.msg
        assert 'Expected: Size(width=200, height=400).' in exc.msg
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_disabled_error_msg(forms_page):
    try:
        forms_page.validation_form.wait_disabled(timeout=timeout)
    except TimeoutException as exc:
        assert f'"Validation form" is not disabled after {timeout} seconds.' in exc.msg
        assert """Selector='xpath=//*[contains(@class, "card") and .//.="Form with Validations"]""" in exc.msg
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_enabled_error_msg(forms_page):
    try:
        forms_page.controls_form.salary_input.wait_enabled(timeout=timeout)
    except TimeoutException as exc:
        assert f'"salary input" is not enabled after {timeout} seconds. ' in exc.msg
        assert """Selector='xpath=//*[contains(@class, "card") and .//.="Basic Form Controls"] >> id=salary'""" in exc.msg
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_non_empty_text_error_msg(forms_page):
    try:
        forms_page.controls_form.salary_input.wait_for_text(timeout=timeout)
    except UnexpectedTextException as exc:
        assert exc.msg == f'Text of "salary input" is empty after {timeout} seconds.'
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_non_empty_value_error_msg(forms_page):
    try:
        forms_page.controls_form.salary_input.wait_for_value(timeout=timeout)
    except UnexpectedValueException as exc:
        assert exc.msg == f'Value of "salary input" is empty after {timeout} seconds.'
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_non_specific_text_error_msg(forms_page):
    try:
        forms_page.controls_form.salary_input.wait_for_text('some text', timeout=timeout)
    except UnexpectedTextException as exc:
        assert exc.msg == f'Not expected text for "salary input" after {timeout} seconds. ' \
                          f'Actual: ""; Expected: "some text".'
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_non_specific_value_error_msg(forms_page):
    try:
        forms_page.controls_form.salary_input.wait_for_value('some value', timeout=timeout)
    except UnexpectedValueException as exc:
        assert exc.msg == f'Not expected value for "salary input" after {timeout} seconds. ' \
                          f'Actual: ""; Expected: "some value".'
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_visible_error_msg(forms_page):
    try:
        forms_page.controls_form.broken_input.wait_visibility(timeout=timeout)
    except TimeoutException as exc:
        assert f'"invalid element" not visible after {timeout} seconds.' in exc.msg
        assert """Selector='xpath=//*[contains(@class, "card") and .//.="Basic Form Controls"] >> id=data'""" in exc.msg
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
@pytest.mark.skip_platform('playwright', reason='selenium only')
def test_get_container_error_msg(forms_page):
    try:
        ExpectedConditionPage().value_card.trigger_button._get_element(wait_strategy=False)
    except NoSuchParentException as exc:
        assert """WaitValueCard container not found while accessing "trigger wait button" Element. Container Selector='xpath=//*[contains(@class, "card") and contains(., "Wait for text")]'""" == exc.msg
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
@pytest.mark.skip_platform('playwright', reason='selenium only')
def test_get_element_error_msg(forms_page):
    try:
        Element('some_element')._get_element(wait_strategy=False)
    except NoSuchElementException as exc:
        assert """Unable to locate the "some_element" Element. Selector='id=some_element'""" == exc.msg
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
@pytest.mark.skip_platform('playwright', reason='selenium only')
def test_get_element_with_element_container_error_msg(forms_page):
    try:
        container = Element(forms_page.controls_form.locator, name='another element as container')
        Element('some_element', parent=container)._get_element(wait_strategy=False)
    except NoSuchElementException as exc:
        assert """Unable to locate the "some_element" Element. Selector='xpath=//*[contains(@class, "card") and .//.="Basic Form Controls"] >> id=some_element'""" in exc.msg, exc.msg
        assert """WARNING: Located 2 elements for "another element as container" container""" in exc.msg, exc.msg
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
@pytest.mark.skip_platform('playwright', reason='selenium only')
def test_get_element_with_container_error_msg(forms_page):
    try:
        forms_page.controls_form.broken_input._get_element(wait_strategy=False)
    except NoSuchElementException as exc:
        assert """Unable to locate the "invalid element" Element. Selector='xpath=//*[contains(@class, "card") and .//.="Basic Form Controls"] >> id=data'""" in exc.msg
        assert """WARNING: Located 2 elements for ControlsForm container""" in exc.msg
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_hidden_error_msg(forms_page):
    try:
        forms_page.controls_form.salary_input.wait_hidden(timeout=timeout)
    except TimeoutException as exc:
        assert f'"salary input" still visible after {timeout} seconds.' in exc.msg
        assert """Selector='xpath=//*[contains(@class, "card") and .//.="Basic Form Controls"] >> id=salary""" in exc.msg
    else:
        raise Exception('Unexpected behaviour')


@pytest.mark.medium
def test_wait_element_available_error_msg(forms_page):
    try:
        forms_page.controls_form.broken_input.wait_availability(timeout=timeout)
    except TimeoutException as exc:
        assert f'"invalid element" not available in DOM after {timeout} seconds.' in exc.msg
        assert """Selector='xpath=//*[contains(@class, "card") and .//.="Basic Form Controls"] >> id=data""" in exc.msg
    else:
        raise Exception('Unexpected behaviour')
