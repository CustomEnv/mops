from types import SimpleNamespace

import pytest
from mops.exceptions import InvalidLocatorException
from mops.mixins.objects.locator import Locator
from mops.utils.selector_synchronizer import get_platform_locator


obj_name = 'namespace(driver_wrapper=namespace'


driver_wrapper_mock = SimpleNamespace(
    is_tablet=False,
    is_android=False,
    is_ios=False,
    is_mobile=False,
    is_desktop=False,
)


@pytest.mark.parametrize('locator', ['tablet', 'android', 'ios', 'mobile', 'desktop'])
def test_missed_platform_locator(locator):
    locator = {locator: None}
    element_obj = SimpleNamespace(driver_wrapper=driver_wrapper_mock, _locator=Locator(**locator))
    try:
        get_platform_locator(element_obj)
    except InvalidLocatorException as exc:
        assert f'Cannot extract locator for current platform for following object: {obj_name}' in exc.msg
    else:
        raise AssertionError('Unexpected behaviour')
