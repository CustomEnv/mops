from __future__ import annotations

from copy import copy
from functools import cache
import inspect
import sys
from typing import TYPE_CHECKING, Any

from selenium.common.exceptions import WebDriverException as SeleniumWebDriverException

from mops.exceptions import DriverWrapperException as MopsDriverWrapperException

if TYPE_CHECKING:
    from collections.abc import Callable

    from mops.base.element import Element
    from mops.base.group import Group
    from mops.base.page import Page
    from mops.mixins.objects.size import Size


WAIT_METHODS_DELAY = 0.1
WAIT_UNIT = 1
WAIT_EL = 10
HALF_WAIT_EL = WAIT_EL / 2
QUARTER_WAIT_EL = HALF_WAIT_EL / 2
WAIT_PAGE = 15


all_tags = frozenset(
    {
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'head',
        'body',
        'input',
        'section',
        'button',
        'a',
        'link',
        'header',
        'div',
        'textarea',
        'svg',
        'circle',
        'iframe',
        'label',
        'p',
        'tr',
        'th',
        'table',
        'tbody',
        'td',
        'select',
        'nav',
        'li',
        'form',
        'footer',
        'frame',
        'area',
        'span',
        'video',
    }
)


def get_dict(obj: Any) -> dict:
    """Return the __dict__ of the given object."""
    return obj.__dict__


def safe_call(func: Callable, *args: Any, **kwargs: Any) -> Any | None:
    """
    Wrap any method that raises internal exceptions to prevent exceptions

    :param func: any internal function
    :param args: any args for function
    :param kwargs: any kwargs for function
    :return: None or function return
    """
    exceptions = (
        MopsDriverWrapperException,
        SeleniumWebDriverException,
    )

    try:
        return func(*args, **kwargs)
    except exceptions:
        pass


@cache
def get_timeout_in_ms(timeout: float) -> float:
    """
    Get timeout in milliseconds for playwright

    :param timeout: timeout in seconds
    :return: timeout in milliseconds
    """
    return validate_timeout(timeout) * 1000


def get_frame(frame: int = 1) -> Any:
    """
    Get frame by given id

    :param frame: frame id, "current" by default
    :return: frame
    """
    return sys._getframe(frame)


def is_element(obj: Any) -> bool:
    """Return True if the given object is an element."""
    return getattr(obj, '_object', None) == 'element'


def is_element_instance(obj: Any) -> bool:
    """Return True if the given object is an element or group."""
    return getattr(obj, '_object', None) in ('element', 'group')


def is_group(obj: Any) -> bool:
    """Return True if the given object is a group."""
    return getattr(obj, '_object', None) == 'group'


def is_page(obj: Any) -> bool:
    """Return True if the given object is a page."""
    return getattr(obj, '_object', None) == 'page'


def is_driver_wrapper(obj: Any) -> bool:
    """Return True if the given object is a driver wrapper."""
    return getattr(obj, '_object', None) == 'driver_wrapper'


def initialize_objects(current_object: Element | Group | Page, sub_elements: dict) -> None:
    """
    Copy objects and initializing them with driver_wrapper from current object

    :param current_object: list of objects to initialize
    :param sub_elements: list of objects to initialize
    :return: None
    """
    for name, obj in sub_elements.items():
        copied_obj = copy(obj)

        promote_parent_element(copied_obj, current_object)
        sub_elements[name] = copied_obj
        setattr(current_object, name, copied_obj(driver_wrapper=current_object.driver_wrapper))
        copied_obj._modify_sub_elements()


def set_parent_for_attr(current_object: Element, with_copy: bool = False) -> None:
    """
    Set parent for all Elements/Group of given class.
    Should be called ONLY in Group object or all_elements method.
    Copy of objects will be executed if with_copy is True. Required for all_elements method

    :param current_object: object of attribute
    :param with_copy: copy child object or not
    :return: self
    """
    current_is_group = is_group(current_object)

    for name, obj in current_object.sub_elements.items():
        element = copy(obj) if with_copy else obj
        if with_copy:
            current_object.sub_elements[name] = element
            setattr(current_object, name, element)

        if (current_is_group and element.parent is None) or is_group(element.parent):
            element.parent = current_object

        if getattr(element, 'sub_elements', None):
            set_parent_for_attr(element, with_copy)


def promote_parent_element(obj: Any, base_obj: Any) -> None:
    """
    Promote parent object in Element if parent is another Element

    :param obj: any element
    :param base_obj: base object of element: Page/Group instance
    :return: None
    """
    initial_parent = obj.parent

    if not initial_parent:
        return

    if is_element_instance(initial_parent) and initial_parent is not base_obj:
        parent_id = initial_parent.__base_obj_id
        for el in base_obj.sub_elements.values():
            if parent_id == el.__base_obj_id:
                obj.parent = el
                break


def extract_named_objects(obj: Any, instance: type | tuple | None = None) -> dict:
    """
    Return all objects of given object or by instance
    Removing parent attribute from list to avoid infinite recursion and all dunder attributes

    :returns: dict of page elements and page objects
    """
    return {
        attribute: value
        for attribute, value in extract_all_named_objects(obj).items()
        if (not instance or isinstance(value, instance)) and not attribute.startswith('__') and attribute != 'parent'
    }


def extract_all_named_objects(reference_obj: Any) -> dict:
    """
    Get attributes from the given object and all its bases.

    :param reference_obj: reference object
    :return: dict of all attributes
    """
    items = {}
    reference_class = reference_obj if inspect.isclass(reference_obj) else reference_obj.__class__
    all_bases = inspect.getmro(reference_class)

    for parent_class in all_bases[-2::-1]:  # Skip the reference class itself
        if parent_class is object or 'ABC' in parent_class.__name__:
            continue

        items.update(get_attributes_from_object(parent_class))

    items.update(get_attributes_from_object(reference_class))
    items.update(get_attributes_from_object(reference_obj))

    return items


def get_attributes_from_object(reference_obj: Any) -> dict:
    """
    Get attributes from the given object.

    :param reference_obj: reference object
    :return: dict of attributes
    """
    return dict(reference_obj.__dict__)


def is_target_on_screen(x: int, y: int, possible_range: Size) -> bool:
    """
    Check is given coordinates fit into given range
    An safe value will be applied due to rounding a number when get size/location of element

    :param x: x coordinate
    :param y: y coordinate
    :param possible_range: possible range
    :return: bool
    """
    safe_value = 2
    return 0 <= x < possible_range.width + safe_value and 0 <= y < possible_range.height + safe_value


def calculate_coordinate_to_click(element: Any, x: int = 0, y: int = 0) -> tuple:
    """
    Calculate coordinates to click for element
    Examples:
        (0, 0) -- center of the element
        (5, 0) -- 5 pixels to the right
        (-10, 0) -- 10 pixels to the left out of the element
        (0, -5) -- 5 pixels below the element

    :param element: mops WebElement or MobileElement
    :param x: horizontal offset relative to either left (x < 0) or right side (x > 0)
    :param y: vertical offset relative to either top (y > 0) or bottom side (y < 0)
    :return: tuple of calculated coordinates
    """
    ey, ex, ew, eh = element.get_rect().values()
    mew, meh = ew / 2, eh / 2
    emx, emy = ex + mew, ey + meh  # middle of element

    sx, sy = ([-1, 1][s > 0] for s in [x, y])
    x = emx + bool(x) * (x + mew * sx)
    y = emy + bool(y) * (y + meh * sy)

    return int(x), int(y)


def validate_timeout(timeout: Any) -> float | int:
    """Validate that timeout is a positive int or float and return it."""
    if type(timeout) not in (int, float):
        msg = 'The type of `timeout` arg must be int or float'
        raise TypeError(msg)

    if timeout <= 0:
        msg = 'The `timeout` value must be a positive number'
        raise ValueError(msg)

    return timeout


def validate_silent(silent: Any) -> bool:
    """Validate that silent is a bool and return it."""
    if not isinstance(silent, bool):
        msg = 'The type of `silent` arg must be bool'
        raise TypeError(msg)

    return silent


def increase_delay(delay: float, max_delay: float = 1.5) -> int | float:
    """Double the delay up to max_delay, then return delay unchanged."""
    if delay < max_delay:
        return delay + delay
    return delay
