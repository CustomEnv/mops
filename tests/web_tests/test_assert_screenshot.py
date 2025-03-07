import os

import pytest
import pytest_rerunfailures
from mops.exceptions import UnexpectedElementsCountException

from mops.mixins.objects.box import Box
from mops.visual_comparison import VisualComparison
from tests.adata.pages.playground_main_page import Card


def safe_call(_callable, _exception):
    try:
        return _callable()
    except _exception:
        pass


@pytest.mark.low
@pytest.mark.parametrize('with_name', [True, False], ids=['screenshot name given', 'screenshot name missed'])
def test_screenshot(base_playground_page, driver_name, platform, with_name):
    filename = f'{driver_name}-{platform}-kube' if with_name else ''
    base_playground_page.kube.scroll_into_view().assert_screenshot(filename)

@pytest.mark.low
@pytest.mark.parametrize('left', [0, 35], ids=['left 0', 'left 35'])
@pytest.mark.parametrize('top', [0, 35], ids=['top 0', 'top 35'])
@pytest.mark.parametrize('right', [0, 35], ids=['right 0', 'right 35'])
@pytest.mark.parametrize('bottom', [0, 35], ids=['bottom 0', 'bottom 35'])
@pytest.mark.parametrize('is_percent', [True, False], ids=['percent value', 'digit value'])
def test_screenshot_with_box(base_playground_page, driver_name, platform, left, top, right, bottom, is_percent):
    """ Task: 16053068 """
    custom_box = Box(left, top, right, bottom, is_percents=is_percent)
    if any([left, top, right, bottom]):
        base_playground_page.kube.scroll_into_view().assert_screenshot(cut_box=custom_box)


@pytest.mark.low
@pytest.mark.parametrize('with_name', [True, False], ids=['screenshot name given', 'screenshot name missed'])
def test_screenshot_name_with_suffix(base_playground_page, driver_name, platform, with_name):
    filename = f'{driver_name}-{platform}-kube' if with_name else ''
    base_playground_page.kube.scroll_into_view().assert_screenshot(filename, name_suffix='first')
    base_playground_page.kube.scroll_into_view().assert_screenshot(filename, name_suffix='second')


def test_screenshot_remove(colored_blocks_page):
    row2_card = colored_blocks_page.row2.card
    cards = row2_card.wait_elements_count(8).all_elements
    colored_blocks_page.row2.assert_screenshot(
        remove=[cards[5], cards[3]],
        delay=0.5,
        scroll=True
    )


@pytest.mark.low
def test_screenshot_popup_with_remove(colored_blocks_page, driver_wrapper):
    overlay_popup = colored_blocks_page.open_popup()
    overlay_popup.assert_screenshot(
        remove=[overlay_popup.popup_text],
    )


@pytest.fixture
def file(request):
    initial_reruns_count = request.node.session.config.option.reruns
    request.node.execution_count = 1
    request.node.session.config.option.reruns = 1
    filename = 'reference_with_rerun'
    yield filename
    request.node.session.config.option.reruns = initial_reruns_count
    if not request.config.option.sv:
        os.remove(f'{os.getcwd()}/tests/adata/visual/reference/{filename}.png')


@pytest.mark.low
def test_screenshot_without_reference_and_rerun(base_playground_page, file, request):
    assert pytest_rerunfailures.get_reruns_count(request.node) == 1
    try:
        base_playground_page.text_container.scroll_into_view(sleep=0.5).assert_screenshot(filename=file)
    except AssertionError:
        pass
    else:
        options = request.config.option
        if not any([options.gr, options.hgr, options.sv, options.sgr]):
            raise Exception('Unexpected behavior')


def test_screenshot_fill_background_blue(colored_blocks_page):
    colored_blocks_page.row1.assert_screenshot(fill_background='blue')


def test_screenshot_fill_background_default(colored_blocks_page):
    colored_blocks_page.row1.assert_screenshot(fill_background=True)


def test_append_dummy_elements_multiple_available(second_playground_page, driver_wrapper):
    """ Case: 65765292 """
    VisualComparison(driver_wrapper)._appends_dummy_elements([Card()])


def test_assert_screenshot_hide_elements(colored_blocks_page, driver_wrapper):
    safe_call(lambda: colored_blocks_page.navbar.wait_elements_count(2), UnexpectedElementsCountException)
    all_cards = colored_blocks_page.get_all_cards()
    colored_blocks_page.row1.assert_screenshot(
        hide=all_cards[1],
        name_suffix='middle hidden',
        delay=0.5,
        scroll=True,
    )
    driver_wrapper.refresh()

    safe_call(lambda: colored_blocks_page.navbar.wait_elements_count(2), UnexpectedElementsCountException)
    all_cards = colored_blocks_page.get_all_cards()
    colored_blocks_page.row1.assert_screenshot(
        hide=[all_cards[0], all_cards[2]],
        name_suffix='sides hidden',
        delay=0.5,
        scroll=True,
    )


@pytest.fixture
def edit_visual_config(request):
    previous_sgr = VisualComparison.soft_visual_reference_generation
    previous_hgr = VisualComparison.hard_visual_reference_generation
    previous_sv = VisualComparison.skip_screenshot_comparison

    VisualComparison.soft_visual_reference_generation = False
    VisualComparison.hard_visual_reference_generation = False
    VisualComparison.skip_screenshot_comparison = False
    yield
    VisualComparison.soft_visual_reference_generation = previous_sgr
    VisualComparison.hard_visual_reference_generation = previous_hgr
    VisualComparison.skip_screenshot_comparison = previous_sv


def test_assert_screenshot_negative_different_sizes(second_playground_page, driver_wrapper, edit_visual_config):
    first_card = second_playground_page.get_all_cards()[0].scroll_into_view()
    vc = VisualComparison(driver_wrapper, element=first_card)
    filename = vc._get_screenshot_name()
    vc._save_screenshot(
        screenshot_name=f'tests/adata/visual/reference/{filename}.png',
        delay=1,
        remove=[],
        fill_background=False,
        cut_box=None,
    )
    driver_wrapper.execute_script('arguments[0].style = "width: 600px"', first_card)
    try:
        first_card.assert_screenshot()
    except AssertionError as exc:
        assert f"Image size (width, height) is not same for '{filename}'" in str(exc)
    else:
        raise Exception('Unexpected behavior')


def test_assert_screenshot_negative_missmatch(second_playground_page, driver_wrapper, edit_visual_config):
    first_card = second_playground_page.get_all_cards()[0].scroll_into_view()
    vc = VisualComparison(driver_wrapper, element=first_card)
    filename = vc._get_screenshot_name()
    vc._save_screenshot(
        screenshot_name=f'tests/adata/visual/reference/{filename}.png',
        delay=1,
        remove=[],
        fill_background=False,
        cut_box=None,
    )
    try:
        first_card.assert_screenshot(fill_background=True)
    except AssertionError as exc:
        assert f"Visual mismatch found for '{filename}'" in str(exc)
    else:
        raise Exception('Unexpected behavior')


def test_assert_screenshot_hide_driver_elements(colored_blocks_page, driver_wrapper):
    safe_call(lambda: colored_blocks_page.navbar.wait_elements_count(2), UnexpectedElementsCountException)
    all_cards = colored_blocks_page.get_all_cards()
    all_cards[0].scroll_into_view()
    driver_wrapper.assert_screenshot(
        hide=[all_cards[1]] + colored_blocks_page.navbar.all_elements,
        name_suffix='middle hidden',
        delay=0.5,
    )
    driver_wrapper.refresh()
    safe_call(lambda: colored_blocks_page.navbar.wait_elements_count(2), UnexpectedElementsCountException)
    all_cards = colored_blocks_page.get_all_cards()
    all_cards[0].scroll_into_view()
    driver_wrapper.assert_screenshot(
        hide=[all_cards[0], all_cards[2]] + colored_blocks_page.navbar.all_elements,
        name_suffix='sides hidden',
        delay=0.5,
    )
