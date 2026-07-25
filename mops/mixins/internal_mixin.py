from __future__ import annotations

from functools import lru_cache
from typing import Any

from mops.utils.internal_utils import (
    extract_all_named_objects,
    extract_named_objects,
)

_shadow_classes: dict[tuple[type, str], type] = {}
_class_configured: dict[type, type] = {}


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
        selector = f'{get_element_info(parent, label="")} >> {selector}'

    return f"{label}'{selector}'" if label else selector


@lru_cache(maxsize=16)
def get_static_attributes(cls: Any) -> dict:
    """Return named objects from the given class using extract_named_objects."""
    return extract_named_objects(cls)


@lru_cache(maxsize=32)
def get_all_static_attributes(cls: Any) -> dict:
    """Return all named objects from the given class using extract_all_named_objects."""
    return extract_all_named_objects(cls)


@lru_cache(maxsize=16)
def get_driver_instance(driver_type: type, instance: type) -> bool:
    """Check if driver_type is a subclass of instance."""
    return issubclass(driver_type, instance)


class InternalMixin:
    driver: None
    driver_wrapper: None

    def _driver_is_instance(self, instance: type) -> bool:
        """Check if the current driver is an instance of the given type."""
        return get_driver_instance(type(self.driver), instance)

    def _safe_setter(self, var: str, value: Any) -> None:
        if not hasattr(self, var):
            setattr(self, var, value)

    def _get_protected_attrs(self: Any, current_obj_cls: type) -> frozenset:
        if '_framework_attrs' not in current_obj_cls.__dict__:
            current_obj_cls._framework_attrs = frozenset(get_all_static_attributes(current_obj_cls))

        return current_obj_cls.__dict__['_framework_attrs']

    def _set_static_main(self, base_cls: type, protected_attrs: set | None = None) -> None:
        if not protected_attrs:
            protected_attrs = self._get_protected_attrs(self.__class__)

        for name, value in get_static_attributes(base_cls).items():
            if name not in protected_attrs:
                setattr(self.__class__, name, value)

    def _set_static(self: Any, cls: type) -> None:
        """
        Copy methods/properties from a driver-specific base class (``WebElement``,
        ``MobileElement``, ``PlayElement``) onto the element's class so they are
        available via normal MRO lookup.

        In multi-driver sessions a per-driver **shadow subclass** is used so that
        each driver type gets its own copy of the methods without polluting the
        original class or other driver's shadow.

        The *protected* attribute set prevents user-defined overrides on subclasses
        (e.g. ``CustomElement.value``) from being overwritten.
        """
        # ── Already configured with this exact driver class → nothing to do ──
        if _class_configured.get(self.__class__) is cls:
            return

        protected = self._get_protected_attrs(self.__class__)

        # ── Multi-driver: isolate driver methods in a shadow subclass ──
        if self.driver_wrapper.session.has_different_driver_types():
            original_class = self.__class__
            target_cls = self._set_shadow_class(protected)

            # Protect only attrs that the user defined *directly on this class*
            # (not inherited attrs which may have been polluted by a previous
            #  driver's ``_set_static`` call on a parent class).
            own_public_attrs = frozenset(k for k in original_class.__dict__ if not k.startswith('_') and k != 'parent')
            protected_attrs = protected & own_public_attrs

        # ── Single driver: set methods directly on the class ──
        else:
            target_cls = self.__class__
            protected_attrs = protected

        # ── Copy —──
        for name, value in get_static_attributes(cls).items():
            if name not in protected_attrs:
                setattr(target_cls, name, value)

        _class_configured[target_cls] = cls

    def _set_shadow_class(self, protected: frozenset) -> type:
        """
        Create or reuse a per-driver shadow subclass. The given *protected*
        set was computed from the original class before any attributes were
        injected, so the shadow class starts with the same baseline.

        :param protected: pre-computed _framework_attrs of the original class.
        :return: the shadow class (a subtype of the original class).
        """
        original_cls = self.__class__
        key = (original_cls, self.driver_wrapper._base_cls.__name__)
        obj_cls = _shadow_classes.get(key)
        if not obj_cls:
            attrs = {'_shadow_class': True, '_framework_attrs': protected}
            obj_cls = type(original_cls.__name__, (original_cls,), attrs)
            _shadow_classes[key] = obj_cls

        self.__class__ = obj_cls

        return obj_cls

    def _repr_builder(self: Any) -> str | None:
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
        except AttributeError:
            return f'{class_name} object at {obj_id}'
        else:
            return f'{base}, {additional_info}'
