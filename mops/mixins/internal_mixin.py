from __future__ import annotations

from functools import lru_cache
from typing import Any

from mops.utils.internal_utils import (
    extract_named_objects,
    extract_all_named_objects,
    is_driver_wrapper,
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
def get_static_attributes(cls: Any) -> dict:
    return extract_named_objects(cls)

@lru_cache(maxsize=32)
def get_all_static_attributes(cls: Any) -> dict:
    return extract_all_named_objects(cls)

@lru_cache(maxsize=16)
def get_driver_instance(driver_type, instance) -> bool:
    return issubclass(driver_type, instance)


class InternalMixin:

    driver: None

    def _driver_is_instance(self, instance):
        return get_driver_instance(type(self.driver), instance)

    def _safe_setter(self, var: str, value: Any):
        if not hasattr(self, var):
            setattr(self, var, value)

    def _get_protected_attrs(self: Any, current_obj_cls) -> set:
        if not is_driver_wrapper(self):
            return set(get_all_static_attributes(current_obj_cls))

        if '_framework_attrs' not in current_obj_cls.__dict__:
            current_obj_cls._framework_attrs = set(get_all_static_attributes(current_obj_cls))

        return current_obj_cls.__dict__['_framework_attrs']

    def _set_static(self: Any, cls) -> None:
        """
        Set static from base cls (Web/Mobile/Play Element/Page etc.)

        :return: None
        """
        current_obj_cls = self.__class__

        if current_obj_cls.__dict__.get('_configured') is cls:
            return

        protected = self._get_protected_attrs(current_obj_cls)

        for name, value in get_static_attributes(cls).items():
            if name not in protected:
                setattr(current_obj_cls, name, value)

        current_obj_cls._configured = cls

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
