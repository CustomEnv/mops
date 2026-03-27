from dataclasses import dataclass


@dataclass
class Size:
    """Represents the dimensions of an object with width and height."""

    width: int | float | None = None
    height: int | float | None = None
