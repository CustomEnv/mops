from selenium.webdriver import Keys as SeleniumSourceKeys

from mops.base.driver_wrapper import DriverWrapper


class SeleniumKeys(SeleniumSourceKeys):
    pass


class PlaywrightKeys:
    """Playwright keyboard key mapping.

    Keys not supported by Playwright (NULL, CANCEL, HELP, CLEAR, RETURN,
    PAUSE, SPACE, SEMICOLON, MULTIPLY, ADD, SEPARATOR, SUBTRACT, DECIMAL,
    DIVIDE, COMMAND, ZENKAKU_HANKAKU) will raise NotImplementedError.
    """

    BACKSPACE = 'Backspace'
    BACK_SPACE = BACKSPACE
    TAB = 'Tab'
    ENTER = 'Enter'
    SHIFT = 'Shift'
    LEFT_SHIFT = SHIFT
    CONTROL = 'Control'
    LEFT_CONTROL = CONTROL
    ALT = 'Alt'
    LEFT_ALT = ALT
    ESCAPE = 'Escape'
    PAGE_UP = 'PageUp'
    PAGE_DOWN = 'PageDown'
    END = 'End'
    HOME = 'Home'
    LEFT = 'ArrowLeft'
    ARROW_LEFT = LEFT
    UP = 'ArrowUp'
    ARROW_UP = UP
    RIGHT = 'ArrowRight'
    ARROW_RIGHT = RIGHT
    DOWN = 'ArrowDown'
    ARROW_DOWN = DOWN
    INSERT = 'Insert'
    DELETE = 'Delete'
    EQUALS = 'Equal'

    NUMPAD0 = 'Digit0'  # number pad keys
    NUMPAD1 = 'Digit1'
    NUMPAD2 = 'Digit2'
    NUMPAD3 = 'Digit3'
    NUMPAD4 = 'Digit4'
    NUMPAD5 = 'Digit5'
    NUMPAD6 = 'Digit6'
    NUMPAD7 = 'Digit7'
    NUMPAD8 = 'Digit8'
    NUMPAD9 = 'Digit9'

    F1 = 'F1'
    F2 = 'F2'
    F3 = 'F3'
    F4 = 'F4'
    F5 = 'F5'
    F6 = 'F6'
    F7 = 'F7'
    F8 = 'F8'
    F9 = 'F9'
    F10 = 'F10'
    F11 = 'F11'
    F12 = 'F12'

    META = 'Meta'


class Interceptor(type):
    def __getattribute__(cls, item: str) -> object:
        if DriverWrapper.is_selenium:
            return getattr(SeleniumKeys, item)
        return getattr(PlaywrightKeys, item, NotImplementedError('Key is not added to Mops framework'))


class KeyboardKeys(SeleniumKeys, PlaywrightKeys, metaclass=Interceptor):
    pass
