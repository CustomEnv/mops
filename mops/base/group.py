from __future__ import annotations

from typing import Any, Union, Optional

from mops.base.driver_wrapper import DriverWrapper
from mops.base.element import Element
from mops.mixins.objects.locator import Locator
from mops.utils.internal_utils import (
    set_parent_for_attr,
    initialize_objects,
    extract_named_objects
)


class Group(Element):
    """
    Represents a group of :class:`.Element`.

    The :class:`.Group` class is an independent class
    that can be used to manage a collection of :class:`.Element` objects.

    However, it can be imported and defined as a class variable
    within a :class:`.Page` or another :class:`.Group` class.
    This allows grouping elements together and interacting with them collectively.

    This class provides functionality for handling element locators,
    initialization with respect to the driver, and managing sub-elements within the group.
    """
    _object: str = 'group'

    def __init__(
            self,
            locator: Union[Locator, str],
            name: str = '',
            parent: Union[Group, Element, bool] = None,
            wait: Optional[bool] = None,
            driver_wrapper: Union[DriverWrapper, Any] = None,
    ):
        """
        Initializes a group of elements based on the current driver.

        If no driver is provided, the initialization will be skipped until
         handled by a :class:`.Page` or :class:`.Group` class.
        The :class:`.Group` class is designed to represent a container for other elements,
         with specific methods to manage child elements, locator handling, and initialization
         with respect to the driver.

        :param locator: The anchor locator for the group. `.LocatorType` is optional.
        :type locator: typing.Union[Locator, str]
        :param name: The name of the group, used for logging and identification purposes.
        :type name: str
        :param parent: The parent group. Provide :obj:`False` to skip the association.
        :type parent: typing.Union[Group, Element, bool]
        :param wait: If set to `True`, the entire group will be checked as
         part of the `wait_page_loaded` and `is_page_opened` methods in the :class:`.Page`.
        :type wait: typing.Optional[bool]
        :param driver_wrapper: The :class:`.DriverWrapper` instance or
         an object containing it to be used for entire group.
        :type driver_wrapper: typing.Union[DriverWrapper, typing.Any]
        """
        super().__init__(
            locator=locator,
            name=name,
            parent=parent,
            wait=wait,
            driver_wrapper=driver_wrapper,
        )

    def _modify_sub_elements(self) -> None:
        """
        Initializing of attributes with type == Group/Element.
        Required for classes with base == Group.
        """
        self.sub_elements = extract_named_objects(self, Element)
        initialize_objects(self, self.sub_elements)
        set_parent_for_attr(self)
