# Wait cases


def test_wait_hidden_without_error_positive(expected_condition_page, caplog):
    assert not expected_condition_page.wait_hidden_card.target_spinner.is_hidden()
    expected_condition_page.wait_hidden_card.trigger_button.click()
    expected_condition_page.wait_hidden_card.target_spinner.wait_hidden_without_error()
    assert expected_condition_page.wait_hidden_card.target_spinner.is_hidden()


def test_wait_visibility_without_error_positive(expected_condition_page, caplog):
    assert not expected_condition_page.wait_visibility_card.target_button.is_displayed()
    expected_condition_page.wait_visibility_card.trigger_button.click()
    expected_condition_page.wait_visibility_card.target_button.wait_visibility_without_error()
    assert expected_condition_page.wait_visibility_card.target_button.is_displayed()


def test_wait_hidden_without_error_negative(expected_condition_page, caplog):
    assert not expected_condition_page.wait_hidden_card.target_spinner.is_hidden()
    expected_condition_page.wait_hidden_card.trigger_button.click()
    expected_condition_page.wait_hidden_card.target_spinner.wait_hidden_without_error(timeout=0.5)
    assert expected_condition_page.wait_hidden_card.target_spinner.is_displayed()
    assert 'Ignored exception:' in str(caplog.messages)


def test_wait_visibility_without_error_negative(expected_condition_page, caplog):
    assert not expected_condition_page.wait_visibility_card.target_button.is_displayed()
    expected_condition_page.wait_visibility_card.trigger_button.click()
    expected_condition_page.wait_visibility_card.target_button.wait_visibility_without_error(timeout=0.5)
    assert expected_condition_page.wait_visibility_card.target_button.is_hidden()
    assert 'Ignored exception:' in str(caplog.messages)


# Continuous wait cases


def test_wait_continuous_hidden_without_error_positive(expected_condition_page, caplog):
    assert not expected_condition_page.wait_hidden_card.target_spinner.is_hidden()
    expected_condition_page.wait_hidden_card.trigger_button.click()
    expected_condition_page.wait_hidden_card.target_spinner.wait_hidden_without_error(continuous=1)
    assert 'Wait until "target spinner" becomes continuous hidden without error exception' in str(caplog.messages)
    assert expected_condition_page.wait_hidden_card.target_spinner.is_hidden()


def test_wait_continuous_visibility_without_error_positive(expected_condition_page, caplog):
    assert not expected_condition_page.wait_visibility_card.target_button.is_displayed()
    expected_condition_page.wait_visibility_card.trigger_button.click()
    expected_condition_page.wait_visibility_card.target_button.wait_visibility_without_error(continuous=1)
    assert 'Wait until "target button" becomes continuous visible without error exception' in str(caplog.messages)
    assert expected_condition_page.wait_visibility_card.target_button.is_displayed()


def test_wait_continuous_hidden_without_error_negative(expected_condition_page, caplog):
    expected_condition_page.blinking_card.set_interval()
    expected_condition_page.blinking_card.blinking_panel.wait_hidden_without_error(continuous=True)
    assert 'The continuous "wait_hidden" of the "blinking panel" is no met after 0.' in str(caplog.messages)
    assert expected_condition_page.blinking_card.blinking_panel.is_displayed()


def test_wait_continuous_visibility_without_error_negative(expected_condition_page, caplog):
    expected_condition_page.blinking_card.set_interval()
    expected_condition_page.blinking_card.blinking_panel.wait_visibility_without_error(continuous=True)
    assert 'The continuous "wait_visibility" of the "blinking panel" is no met after 0.' in str(caplog.messages)
    assert expected_condition_page.blinking_card.blinking_panel.is_hidden()
