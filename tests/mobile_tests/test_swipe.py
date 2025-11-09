def test_swipe(second_playground_page, driver_wrapper):
    expected_scroll = range(300, 400) if driver_wrapper.is_android else range(1050, 1200)
    second_playground_page.swipe(0, 500, 0, 100, sleep=0.3)
    scroll = driver_wrapper.get_scroll_position()
    assert scroll in expected_scroll
    second_playground_page.swipe(0, 100, 0, 500, sleep=0.3)
    scroll = driver_wrapper.get_scroll_position()
    assert scroll == 0
