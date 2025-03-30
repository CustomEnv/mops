from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

from mops.base.element import Element
from mops.utils.internal_utils import (
    get_child_elements,
    get_child_elements_with_names,
    initialize_objects,
    set_parent_for_attr,
)

if TYPE_CHECKING:
    from mops.base.driver_wrapper import DriverWrapper
    from mops.mixins.objects.locator import Locator


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

    _object = 'group'

    def __repr__(self):
        return self._repr_builder()

    def __init__(
            self,
            locator: Union[Locator, str],
            name: str = '',
            parent: Union[Group, Element, bool] = None,
            wait: Optional[bool] = None,
            driver_wrapper: Union[DriverWrapper, Any] = None,
    ):
        """
        Initialize a group of elements based on the current driver.

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
        self._init_locals = locals()
        super().__init__(
            locator=locator,
            name=name,
            parent=parent,
            wait=wait,
            driver_wrapper=driver_wrapper,
        )

    def _modify_children(self) -> None:
        """
        Initialize of attributes with type == Group/Element.
        Required for classes with base == Group.
        """
        initialize_objects(self, get_child_elements_with_names(self, Element), Element)
        set_parent_for_attr(self, Element)
        self.child_elements: List[Element] = get_child_elements(self, Element)
