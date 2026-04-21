def test_set_local_storage_item(driver_wrapper, second_playground_page):
    driver_wrapper.set_local_storage_item([{'key': 'ls_key', 'value': 'ls_value'}])

    assert driver_wrapper.get_local_storage_item('ls_key') == 'ls_value'


def test_set_local_storage_items_multiple(driver_wrapper, second_playground_page):
    driver_wrapper.set_local_storage_item([
        {'key': 'ls_a', 'value': 'aaa'},
        {'key': 'ls_b', 'value': 'bbb'},
    ])
    items = driver_wrapper.get_local_storage_items()

    assert items.get('ls_a') == 'aaa'
    assert items.get('ls_b') == 'bbb'


def test_get_local_storage_item_missing(driver_wrapper, second_playground_page):
    assert driver_wrapper.get_local_storage_item('nonexistent_key') is None


def test_set_session_storage_item(driver_wrapper, second_playground_page):
    driver_wrapper.set_session_storage_item([{'key': 'ss_key', 'value': 'ss_value'}])

    assert driver_wrapper.get_session_storage_item('ss_key') == 'ss_value'


def test_set_session_storage_items_multiple(driver_wrapper, second_playground_page):
    driver_wrapper.set_session_storage_item([
        {'key': 'ss_a', 'value': 'aaa'},
        {'key': 'ss_b', 'value': 'bbb'},
    ])
    items = driver_wrapper.get_session_storage_items()

    assert items.get('ss_a') == 'aaa'
    assert items.get('ss_b') == 'bbb'


def test_get_session_storage_item_missing(driver_wrapper, second_playground_page):
    assert driver_wrapper.get_session_storage_item('nonexistent_key') is None


def test_remove_local_storage_item(driver_wrapper, second_playground_page):
    driver_wrapper.set_local_storage_item([
        {'key': 'ls_keep', 'value': '1'},
        {'key': 'ls_remove', 'value': '2'},
    ])
    driver_wrapper.remove_local_storage_item('ls_remove')

    assert driver_wrapper.get_local_storage_item('ls_keep') == '1'
    assert driver_wrapper.get_local_storage_item('ls_remove') is None


def test_remove_session_storage_item(driver_wrapper, second_playground_page):
    driver_wrapper.set_session_storage_item([
        {'key': 'ss_keep', 'value': '1'},
        {'key': 'ss_remove', 'value': '2'},
    ])
    driver_wrapper.remove_session_storage_item('ss_remove')

    assert driver_wrapper.get_session_storage_item('ss_keep') == '1'
    assert driver_wrapper.get_session_storage_item('ss_remove') is None


def test_clear_local_storage(driver_wrapper, second_playground_page):
    driver_wrapper.set_local_storage_item([
        {'key': 'ls_a', 'value': 'aaa'},
        {'key': 'ls_b', 'value': 'bbb'},
    ])
    driver_wrapper.clear_local_storage()

    assert driver_wrapper.get_local_storage_items() == {}


def test_clear_session_storage(driver_wrapper, second_playground_page):
    driver_wrapper.set_session_storage_item([
        {'key': 'ss_a', 'value': 'aaa'},
        {'key': 'ss_b', 'value': 'bbb'},
    ])
    driver_wrapper.clear_session_storage()

    assert driver_wrapper.get_session_storage_items() == {}
