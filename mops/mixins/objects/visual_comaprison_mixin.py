from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mops.base.driver_wrapper import DriverWrapper
    from mops.base.element import Element


def hide_elements(objects_to_hide: list[Element] | Element, is_optional: bool, dw: DriverWrapper) -> None:
    for object_to_hide in objects_to_hide:

        if is_optional:
            object_to_hide = object_to_hide(dw)
            if object_to_hide.is_displayed(silent=True):
                object_to_hide.hide(silent=True)
        else:
            object_to_hide.hide(silent=True)



def hide_before_screenshot(objects_to_hide: list | Any, is_optional: bool, dw: DriverWrapper = None) -> None:
    if objects_to_hide:
        if not isinstance(objects_to_hide, list):
            objects_to_hide = [objects_to_hide]

        hide_elements(objects_to_hide, is_optional=is_optional, dw=dw)


def reveal_after_screenshot(objects_to_reveal: list | Any, dw: DriverWrapper) -> None:
    for object_to_reveal in objects_to_reveal:
        object_to_reveal = object_to_reveal(dw)
        if object_to_reveal.is_displayed(silent=True):
            object_to_reveal.show(silent=True)
