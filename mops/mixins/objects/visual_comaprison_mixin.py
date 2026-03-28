from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mops.base.driver_wrapper import DriverWrapper
    from mops.base.element import Element


def hide_elements(objects_to_hide: list[Element] | Element, is_optional: bool, dw: DriverWrapper) -> None:
    """Hide all elements in the given list, optionally checking visibility first."""
    for object_to_hide in objects_to_hide:
        if is_optional:
            element = object_to_hide(dw)
            if element.is_displayed(silent=True):
                element.hide(silent=True)
        else:
            object_to_hide.hide(silent=True)


def hide_before_screenshot(objects_to_hide: list | Any, is_optional: bool, dw: DriverWrapper = None) -> None:
    """Hide the given elements before taking a screenshot."""
    if objects_to_hide:
        if not isinstance(objects_to_hide, list):
            objects_to_hide = [objects_to_hide]

        hide_elements(objects_to_hide, is_optional=is_optional, dw=dw)


def reveal_after_screenshot(objects_to_reveal: list | Any, dw: DriverWrapper) -> None:
    """Reveal all previously hidden elements after the screenshot is taken."""
    for object_to_reveal in objects_to_reveal:
        element = object_to_reveal(dw)
        if element.is_displayed(silent=True):
            element.show(silent=True)
