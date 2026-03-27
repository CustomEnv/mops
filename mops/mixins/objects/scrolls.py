class ScrollTo:
    """Defines available scroll positioning options."""

    START: str = 'start'
    CENTER: str = 'center'
    END: str = 'end'
    NEAREST: str = 'nearest'


class ScrollTypes:
    """Defines available scroll behaviors."""

    SMOOTH: str = 'smooth'
    INSTANT: str = 'instant'


scroll_into_view_blocks = (ScrollTo.START, ScrollTo.CENTER, ScrollTo.END, ScrollTo.NEAREST)
