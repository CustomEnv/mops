from __future__ import annotations

import sys
import inspect
from copy import copy
from functools import lru_cache
from typing import Any, Union, Callable

from selenium.common.exceptions import WebDriverException as SeleniumWebDriverException

from mops.exceptions import DriverWrapperException as MopsDriverWrapperException
from mops.mixins.objects.size import Size

WAIT_METHODS_DELAY = 0.1
WAIT_UNIT = 1
WAIT_EL = 10
HALF_WAIT_EL = WAIT_EL / 2
QUARTER_WAIT_EL = HALF_WAIT_EL / 2
WAIT_PAGE = 15


all_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'head', 'body', 'input', 'section', 'button', 'a', 'link', 'header', 'div',
            'textarea', 'svg', 'circle', 'iframe', 'label', 'p', 'tr', 'th', 'table', 'tbody', 'td', 'select', 'nav',
            'li', 'form', 'footer', 'frame', 'area', 'span', 'video'}


def get_dict(obj: Any):
    return obj.__dict__


def safe_call(func: Callable, *args, **kwargs) -> Union[Any, None]:
    """
    Wrapper for any method that raises internal exceptions to prevent exceptions

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


@lru_cache(maxsize=None)
def get_timeout_in_ms(timeout: Union[int, float]):
    """
    Get timeout in milliseconds for playwright

    :param timeout: timeout in seconds
    :return: timeout in milliseconds
    """
    return validate_timeout(timeout) * 1000


def safe_getattribute(obj, item):
    return object.__getattribute__(obj, item)


def get_frame(frame=1):
    """
    Get frame by given id

    :param frame: frame id, "current" by default
    :return: frame
    """
    return sys._getframe(frame)  # noqa


def is_element(obj: Any) -> bool:
    return getattr(obj, '_object', None) == 'element'


def is_element_instance(obj: Any) -> bool:
    return getattr(obj, '_object', None) in ('element', 'group')


def is_group(obj: Any) -> bool:
    return getattr(obj, '_object', None) == 'group'


def is_page(obj: Any) -> bool:
    return getattr(obj, '_object', None) == 'page'


def is_driver_wrapper(obj: Any) -> bool:
    return getattr(obj, '_object', None) == 'driver_wrapper'


def initialize_objects(current_object, objects: dict, cls: Any):
    """
    Copy objects and initializing them with driver_wrapper from current object

    :param current_object: list of objects to initialize
    :param objects: list of objects to initialize
    :param cls: class of initializing objects
    :return: None
    """
    for name, obj in objects.items():
        copied_obj = copy(obj)
        promote_parent_element(copied_obj, current_object, cls)
        setattr(current_object, name, copied_obj(driver_wrapper=current_object.driver_wrapper))
        initialize_objects(copied_obj, get_child_elements_with_names(copied_obj, cls), cls)


def set_parent_for_attr(base_obj: object, instance_class: Union[type, tuple], with_copy: bool = False):
    """
    Sets parent for all Elements/Group of given class.
    Should be called ONLY in Group object or all_elements method.
    Copy of objects will be executed if with_copy is True. Required for all_elements method

    :param instance_class: attribute class to looking for
    :param base_obj: object of attribute
    :param with_copy: copy child object or not
    :return: self
    """
    child_elements = get_child_elements_with_names(base_obj, instance_class).items()

    for name, child in child_elements:
        if with_copy:
            child = copy(child)

        if (is_group(base_obj) and child.parent is None) or is_group(child.parent):
            child.parent = base_obj

        if with_copy:
            setattr(base_obj, name, child)

        set_parent_for_attr(child, instance_class, with_copy)


def promote_parent_element(obj: Any, base_obj: Any, cls: Any):
    """
    Promote parent object in Element if parent is another Element

    :param obj: any element
    :param base_obj: base object of element: Page/Group instance
    :param cls: element class
    :return: None
    """
    initial_parent = getattr(obj, 'parent', None)

    if not initial_parent:
        return None

    if is_element_instance(initial_parent) and initial_parent != base_obj:
        for el in get_child_elements(base_obj, cls):
            if obj.parent.__base_obj_id == el.__base_obj_id:
                obj.parent = el


def get_child_elements(obj: object, instance: Union[type, tuple]) -> list:
    """
    Return objects of this object by instance

    :returns: list of page elements and page objects
    """
    return list(get_child_elements_with_names(obj, instance).values())


def get_child_elements_with_names(obj: Any, instance: Union[type, tuple] = None) -> dict:
    """
    Return all objects of given object or by instance
    Removing parent attribute from list to avoid infinite recursion and all dunder attributes

    :returns: dict of page elements and page objects
    """
    elements = {}

    for attribute, value in get_all_attributes_from_object(obj).items():
        if instance and isinstance(value, instance) or not instance:
            if attribute != 'parent' and not attribute.startswith('__') and not attribute.endswith('__'):
                elements.update({attribute: value})

    return elements


def get_all_attributes_from_object(reference_obj: Any) -> dict:
    """
    Get attributes from given object and all its bases

    :param reference_obj: reference object
    :return: dict of all attributes
    """
    items = {}

    if not reference_obj:
        return items

    reference_class = reference_obj if inspect.isclass(reference_obj) else reference_obj.__class__
    all_bases = list(inspect.getmro(reference_class))
    all_bases.reverse()  # Reverse needed for collect subclasses attributes as base one

    for parent_class in all_bases:

        if 'ABC' in str(parent_class) or parent_class == object:
            continue

        items.update(dict(parent_class.__dict__))

    return {**items, **get_attributes_from_object(reference_obj)}


def get_attributes_from_object(reference_obj: Any) -> dict:
    """
    Get attributes from given object

    :param reference_obj:
    :return:
    """
    items = {}

    if not reference_obj:
        return items

    if not inspect.isclass(reference_obj):
        items.update(dict(reference_obj.__class__.__dict__))

    items.update(dict(reference_obj.__dict__))

    return items


def is_target_on_screen(x: int, y: int, possible_range: Size):
    """
    Check is given coordinates fit into given range
    An safe value will be applied:
      1 - Due to usage of range
      2 - Due to rounding a number when get size/location of element

    :param x: x coordinate
    :param y: y coordinate
    :param possible_range: possible range
    :return: bool
    """
    safe_value = 2
    is_x_on_screen = x in range(possible_range.width + safe_value)
    is_y_on_screen = y in range(possible_range.height + safe_value)
    return is_x_on_screen and is_y_on_screen


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


def validate_timeout(timeout) -> Union[float, int]:
    if type(timeout) not in (int, float):
        raise TypeError('The type of `timeout` arg must be int or float')

    if timeout <= 0:
        raise ValueError('The `timeout` value must be a positive number')

    return timeout


def validate_silent(silent) -> bool:
    if not isinstance(silent, bool):
        raise TypeError(f'The type of `silent` arg must be bool')

    return silent


def increase_delay(delay, max_delay: Union[int, float] = 1.5) -> Union[int, float]:
    if delay < max_delay:
        return delay + delay
    return delay
