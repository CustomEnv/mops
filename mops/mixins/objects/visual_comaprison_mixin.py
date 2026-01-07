from __future__ import annotations

from typing import Union, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from mops.base.element import Element
    from mops.base.driver_wrapper import DriverWrapper


def hide_elements(objects_to_hide: Union[list[Element], Element], is_optional: bool, dw: DriverWrapper):
    for object_to_hide in objects_to_hide:

        if is_optional:
            object_to_hide = object_to_hide(dw)
            if object_to_hide.is_displayed(silent=True):
                object_to_hide.hide(silent=True)
        else:
            object_to_hide.hide(silent=True)



def hide_before_screenshot(objects_to_hide: Union[list, Any], is_optional: bool, dw: DriverWrapper = None):
    if objects_to_hide:
        if not isinstance(objects_to_hide, list):
            objects_to_hide = [objects_to_hide]

        hide_elements(objects_to_hide, is_optional=is_optional, dw=dw)


def reveal_after_screenshot(objects_to_reveal: Union[list, Any], dw: DriverWrapper):
    for object_to_reveal in objects_to_reveal:
        object_to_reveal = object_to_reveal(dw)
        if object_to_reveal.is_displayed(silent=True):
            object_to_reveal.show(silent=True)
