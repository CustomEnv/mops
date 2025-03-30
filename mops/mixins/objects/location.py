from dataclasses import dataclass
import typing


@dataclass
class Location:
    """Represents a location on a web UI element, defined by its `x` and `y` coordinates."""

    x: typing.Union[int, float, None] = None
    y: typing.Union[int, float, None] = None
