from dataclasses import dataclass


@dataclass
class Location:
    """Represents a location on a web UI element, defined by its `x` and `y` coordinates."""

    x: int | float | None = None
    y: int | float | None = None
