import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutException

from mops.exceptions import TimeoutException
from tests.adata.pages.mouse_event_page import MouseEventPageWithUnexpectedWait


@pytest.mark.parametrize('with_elements_case', (True, False), ids=['with elements', 'without elements'])
def test_page_loaded_positive(mouse_event_page_v2, with_elements_case):
    mouse_event_page_v2.wait_page_loaded()
    assert mouse_event_page_v2.is_page_opened(with_elements=with_elements_case)


@pytest.mark.parametrize('with_elements_case', (True, False), ids=['with elements', 'without elements'])
def test_page_loaded_negative(mouse_event_page_v2, with_elements_case):
    page = MouseEventPageWithUnexpectedWait()
    try:
        page.wait_page_loaded(timeout=0.1)
    except (TimeoutException, PlaywrightTimeoutException):
        if with_elements_case:
            assert not page.is_page_opened(with_elements=with_elements_case)
        else:
            assert page.is_page_opened(with_elements=with_elements_case)
    else:
        raise pytest.fail('Unexpected behavior. Case not covered')
