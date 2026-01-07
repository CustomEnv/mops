import cProfile
import pstats
import sys
import tracemalloc
import time

import pytest

from mops.base.element import Element
from mops.base.group import Group
from mops.base.page import Page
from mops.shared_utils import get_all_sub_elements

section_sub_elements_count = 5000


class AnotherSection1(Group):

    def __init__(self):
        super().__init__('AnotherSection')


class AnotherSection(Group):

    def __init__(self):
        super().__init__('AnotherSection')

    another_some_element = Element('AnotherSection_another_some_element')


class SomeSection(Group):

    def __init__(self, locator):
        super().__init__(locator)

    AnotherSection = AnotherSection()


class SomePage(Page):

    def __init__(self, driver_wrapper = None):
        super().__init__('SomePage', driver_wrapper=driver_wrapper)



@pytest.fixture(scope='module')
def set_elements_class_var_objects():
    for _i in range(section_sub_elements_count):
        _element = Element(f'{_i}_element')
        setattr(AnotherSection1, _element.name, _element)


@pytest.mark.parametrize('case', range(5))
def test_performance_element_initialisation(mocked_selenium_driver, case, set_elements_class_var_objects):
    tracemalloc.start()
    start_cpu = time.process_time()

    with cProfile.Profile() as pr:
        section = AnotherSection1()

    end_cpu = time.process_time()
    cpu_time = end_cpu - start_cpu  # CPU time used

    peak_mem = tracemalloc.get_traced_memory()[1] / 1024**2
    tracemalloc.stop()

    stats: pstats.Stats = pstats.Stats(pr)
    stats.strip_dirs().sort_stats("time").print_stats(20)

    init_without_profiling_start_timestamp = time.time()
    AnotherSection1()
    init_without_profiling_stop_timestamp = time.time() - init_without_profiling_start_timestamp

    print('stats.total_tt=', stats.total_tt)
    print('peak_mem=', peak_mem)
    print('cpu_time=', cpu_time)
    print('init_without_profiling_stop_timestamp=', init_without_profiling_stop_timestamp)

    expected_peak_mem = 4.7
    expected_init_duration = 0.4
    init_without_profiling_expected = 0.1

    if sys.version_info >= (3, 9):
        expected_peak_mem = 4.7
        expected_init_duration = 0.4
        init_without_profiling_expected = 0.13
    if sys.version_info >= (3, 10):
        expected_peak_mem = 4.6
        expected_init_duration = 0.4
    if sys.version_info >= (3, 11):
        expected_peak_mem = 4.0
        expected_init_duration = 0.4
    if sys.version_info >= (3, 12):
        expected_peak_mem = 3.8
        expected_init_duration = 0.4

    assert init_without_profiling_stop_timestamp < init_without_profiling_expected,\
        f'Execution without profiling takes too much time: {init_without_profiling_stop_timestamp}'
    assert expected_init_duration -0.25 < stats.total_tt < expected_init_duration,\
        f"Execution time too high: {stats.total_tt:.3f} sec"
    assert expected_peak_mem - 0.8 < peak_mem < expected_peak_mem,\
        f"Peak memory usage too high: {peak_mem:.2f} MB"
    assert len(section.sub_elements) == section_sub_elements_count, \
        f"Expected {section_sub_elements_count} elements, got {len(section.sub_elements)}"
    assert cpu_time < expected_init_duration, f"CPU execution time too high: {cpu_time:.3f} sec"


@pytest.fixture(scope='module')
def set_groups_class_var_objects():
    for _i in range(20):
        _element = Element(f'AnotherSection_another_some_element_{_i}')
        setattr(AnotherSection, _element.name, _element)

    for _i in range(50):
        _element = Element(f'SomeSection_some_element_{_i}')
        setattr(SomeSection, _element.name, _element)

    for _i in range(50):
        _section = SomeSection(f'{_i}_SomeSection')
        setattr(SomePage, _section.name, _section)


@pytest.mark.parametrize('case', range(5))
def test_performance_group_initialisation(mocked_selenium_driver, case, set_groups_class_var_objects):

    tracemalloc.start()
    start_cpu = time.process_time()

    with cProfile.Profile() as pr:
        page = SomePage()

    end_cpu = time.process_time()
    cpu_time = end_cpu - start_cpu  # CPU time used

    peak_mem = tracemalloc.get_traced_memory()[1] / 1024**2
    tracemalloc.stop()

    stats: pstats.Stats = pstats.Stats(pr)
    stats.strip_dirs().sort_stats("time").print_stats(200)

    count = len(get_all_sub_elements(page))
    init_without_profiling_start_timestamp = time.time()
    SomePage()
    init_without_profiling_stop_timestamp = time.time() - init_without_profiling_start_timestamp

    print('stats.total_tt=', stats.total_tt)
    print('peak_mem=', peak_mem)
    print('cpu_time=', cpu_time)
    print('init_without_profiling_stop_timestamp=', init_without_profiling_stop_timestamp)

    expected_peak_mem = 3.2
    expected_init_duration = 0.4

    if sys.version_info >= (3, 9):
        expected_peak_mem = 3.5
        expected_init_duration = 0.4

    if sys.version_info >= (3, 10):
        expected_peak_mem = 3.3
        expected_init_duration = 0.4

    if sys.version_info >= (3, 11):
        expected_peak_mem = 2.6
        expected_init_duration = 0.4

    if sys.version_info >= (3, 12):
        expected_peak_mem = 2.5
        expected_init_duration = 0.4

    assert init_without_profiling_stop_timestamp < 0.15,\
        f'Execution without profiling takes too much time: {init_without_profiling_stop_timestamp}'
    assert expected_init_duration -0.25 < stats.total_tt < expected_init_duration, \
        f"Execution time too high: {stats.total_tt:.3f} sec"
    assert expected_peak_mem -0.8 < peak_mem < expected_peak_mem, \
        f"Peak memory usage too high: {peak_mem:.2f} MB"
    assert cpu_time < expected_init_duration, f"CPU execution time too high: {cpu_time:.3f} sec"
    assert count > 3600, f"Expected 3600 elements, got {count}"