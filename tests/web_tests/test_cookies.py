DOMAIN = '.customenv.github.io'


def test_set_cookie_sets_cookies(driver_wrapper, second_playground_page):
    driver_wrapper.set_cookie([{'name': 'sample_cookie', 'value': '123', 'domain': DOMAIN}])
    cookies = driver_wrapper.get_cookies()
    driver_wrapper.clear_cookies()

    assert any(c['name'] == 'sample_cookie' and c['value'] == '123' for c in cookies)
    assert not driver_wrapper.get_cookies()


def test_set_cookie_multiple(driver_wrapper, second_playground_page):
    driver_wrapper.set_cookie([
        {'name': 'cookie_a', 'value': 'aaa', 'domain': DOMAIN},
        {'name': 'cookie_b', 'value': 'bbb', 'domain': DOMAIN},
    ])
    cookies = driver_wrapper.get_cookies()
    names = {c['name'] for c in cookies}
    driver_wrapper.clear_cookies()

    assert {'cookie_a', 'cookie_b'}.issubset(names)


def test_set_cookie_does_not_mutate_input(driver_wrapper, second_playground_page):
    cookie = {'name': 'no_mutation', 'value': 'x', 'domain': DOMAIN}
    original_keys = set(cookie.keys())

    driver_wrapper.set_cookie([cookie])
    driver_wrapper.clear_cookies()

    assert set(cookie.keys()) == original_keys


def test_set_cookie_default_path(driver_wrapper, second_playground_page):
    cookie_without_path = {'name': 'path_cookie', 'value': '1', 'domain': DOMAIN}

    driver_wrapper.set_cookie([cookie_without_path])
    cookies = driver_wrapper.get_cookies()
    driver_wrapper.clear_cookies()

    match = next((c for c in cookies if c['name'] == 'path_cookie'), None)
    assert match is not None
    assert match.get('path') == '/'


def test_delete_cookie_removes_target(driver_wrapper, second_playground_page):
    driver_wrapper.set_cookie([
        {'name': 'keep_me', 'value': '1', 'domain': DOMAIN},
        {'name': 'delete_me', 'value': '2', 'domain': DOMAIN},
    ])
    driver_wrapper.delete_cookie('delete_me')
    remaining = driver_wrapper.get_cookies()
    names = {c['name'] for c in remaining}
    driver_wrapper.clear_cookies()

    assert 'delete_me' not in names
    assert 'keep_me' in names


def test_delete_cookie_leaves_others_intact(driver_wrapper, second_playground_page):
    driver_wrapper.set_cookie([
        {'name': 'alpha', 'value': 'aaa', 'domain': DOMAIN},
        {'name': 'beta', 'value': 'bbb', 'domain': DOMAIN},
        {'name': 'gamma', 'value': 'ccc', 'domain': DOMAIN},
    ])
    driver_wrapper.delete_cookie('beta')
    remaining = driver_wrapper.get_cookies()
    names = {c['name'] for c in remaining}
    driver_wrapper.clear_cookies()

    assert 'beta' not in names
    assert {'alpha', 'gamma'}.issubset(names)


def test_delete_cookie_only_one(driver_wrapper, second_playground_page):
    driver_wrapper.set_cookie([{'name': 'solo', 'value': 'x', 'domain': DOMAIN}])
    driver_wrapper.delete_cookie('solo')

    assert not driver_wrapper.get_cookies()


def test_delete_nonexistent_cookie_does_not_raise(driver_wrapper, second_playground_page):
    driver_wrapper.delete_cookie('nonexistent_cookie')
