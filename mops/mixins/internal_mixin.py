from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

from appium.webdriver.common.appiumby import AppiumBy

from mops.utils.internal_utils import (
    get_all_attributes_from_object,
    get_child_elements,
    get_child_elements_with_names,
)

all_locator_types = get_child_elements(AppiumBy, str)
available_kwarg_keys = ('desktop', 'mobile', 'ios', 'android')


def get_element_info(element: Any, label: str = 'Selector=') -> str:
    """
    Get element selector information with parent object selector if it exists.

    :param element: element to collect log data
    :param label: a label before selector string
    :return: log string
    """
    selector = element.log_locator
    parent = element.parent

    if parent:
        selector = f"{get_element_info(parent, label='')} >> {selector}"

    return f"{label}'{selector}'" if label else selector

@lru_cache(maxsize=16)
def get_static(cls: Any):
    return get_child_elements_with_names(cls).items()

class InternalMixin:

    def _safe_setter(self, var: str, value: Any) -> None:
        if not hasattr(self, var):
            setattr(self, var, value)

    def _set_static(self: Any, cls) -> None:
        """
        Set static from base cls (Web/Mobile/Play Element/Page etc.).

        :return: None
        """
        data = {
            name: value for name, value in get_static(cls)
            if name not in get_all_attributes_from_object(self)
        }.items()

        for name, item in data:
            setattr(self.__class__, name, item)

    def _repr_builder(self: Any) -> Optional[str]:
        class_name = self.__class__.__name__
        obj_id = hex(id(self))
        parent = getattr(self, 'parent', False)

        try:
            parent_class = self.parent.__class__.__name__ if parent else None
            locator_holder = getattr(self, 'anchor', self)

            locator = f'locator="{locator_holder.log_locator}", '
            name = f'name="{self.name}", '
            parent = f'parent={parent_class}'
            driver = f'{self.driver_wrapper.label}={self.driver}'

            base = f'{class_name}({locator}{name}{parent}) at {obj_id}'
            additional_info = driver
            return f'{base}, {additional_info}'
        except AttributeError:
            return f'{class_name} object at {obj_id}'
