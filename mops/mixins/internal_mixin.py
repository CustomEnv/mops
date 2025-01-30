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
def get_static_with_bases(cls: Any) -> dict:
    return get_child_elements_with_names(cls)

@lru_cache(maxsize=64)
def get_static_without_bases(cls: Any) -> dict:
    return get_all_attributes_from_object(cls)

@lru_cache(maxsize=16)
def get_driver_instance(driver, instance) -> bool:
    return isinstance(driver, instance)

class InternalMixin:

    driver: None

    def _get_driver_instance(self, instance):
        return get_driver_instance(self.driver, instance)

    def _safe_setter(self, var: str, value: Any):
        if not hasattr(self, var):
            setattr(self, var, value)

    def _set_static(self: Any, cls) -> None:
        """
        Set static from base cls (Web/Mobile/Play Element/Page etc.)

        :return: None
        """
        current_obj_cls = self.__class__
        data = {
            name: value for name, value in get_static_with_bases(cls).items()
            if name not in get_static_without_bases(current_obj_cls)
        }.items()

        for name, item in data:
            setattr(current_obj_cls, name, item)

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
