from __future__ import annotations

from dataclasses import InitVar, dataclass
import typing

from mops.utils.internal_utils import get_dict

if typing.TYPE_CHECKING:
    from mops.mixins.objects.size import Size


@dataclass
class Box:
    """
    Represents a rectangular region defined by its edges: left, top, right, and bottom.

    The class allows specifying these edges as absolute values or percentages of an image's dimensions.
    It includes methods to fill missing values and calculate the coordinates of the cut box based on an image's size.
    """

    left: typing.Union[int, float, None] = None
    top: typing.Union[int, float, None] = None
    right: typing.Union[int, float, None] = None
    bottom: typing.Union[int, float, None] = None
    is_percents: InitVar[bool] = False

    def __post_init__(self, is_percents: InitVar[bool]):
        self.is_percents = is_percents  # is_percents will be ignored in `fields` and other dataclasses methods

    def fill_values(self) -> None:
        """
        Replaces :obj:`None` values for the cut box edges with `0`.

        This method ensures that all edges (left, top, right, bottom) have valid numerical values,
        defaulting to zero where no value is provided.

        :return: :obj:`None`
        """
        for name, value in get_dict(self).items():
            setattr(self, name, value if value else 0)

    def get_image_cut_box(self, size: Size) -> Box:
        """
        Calculates the cut box coordinates based on the provided image dimensions.

        This method computes the values of the left, top, right, and bottom edges,
        adjusting for whether the values are absolute or percentages of the image's size.

        :param size: :class:`.Size` object containing the width and height of the image size.
        :type size: Size
        :return: New :obj:`.Box` object representing the coordinates of the cut box (left, top, right, bottom).
        """
        width, height = size.width, size.height
        self.fill_values()

        if self.is_percents:
            left = self.left * width / 100 if self.left else self.left
            top = self.top * height / 100 if self.top else self.top
            right = width - self.right * width / 100 if self.right else width
            bottom = height - self.bottom * height / 100 if self.bottom else height
            return Box(left=left, top=top, right=right, bottom=bottom)

        return Box(left=self.left, top=self.top, right=width-self.right, bottom=height-self.bottom)

