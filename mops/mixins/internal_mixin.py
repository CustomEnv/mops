from __future__ import annotations

from functools import lru_cache
from typing import Any

from mops.utils.internal_utils import (
    get_child_elements_with_names,
    get_all_attributes_from_object,
)


def get_element_info(element: Any, label: str = 'Selector=') -> str:
    """
    Get element selector information with parent object selector if it exists

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

    def _safe_setter(self, var: str, value: Any):
        if not hasattr(self, var):
            setattr(self, var, value)

    def _set_static(self: Any, cls) -> None:
        """
        Set static from base cls (Web/Mobile/Play Element/Page etc.)

        :return: None
        """
        data = {
            name: value for name, value in get_static(cls)
            if name not in get_all_attributes_from_object(self).keys()
        }.items()

        for name, item in data:
            setattr(self.__class__, name, item)

    def _repr_builder(self: Any):
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
