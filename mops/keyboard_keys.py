from selenium.webdriver import Keys as SeleniumSourceKeys

from mops.base.driver_wrapper import DriverWrapper


class SeleniumKeys(SeleniumSourceKeys):
    pass


class PlaywrightKeys:

    # NULL = '\ue000'
    # CANCEL = '\ue001'  # ^break
    # HELP = '\ue002'
    BACKSPACE = 'Backspace'
    BACK_SPACE = BACKSPACE
    TAB = 'Tab'
    # CLEAR = '\ue005'
    # RETURN = '\ue006'
    ENTER = 'Enter'
    SHIFT = 'Shift'
    LEFT_SHIFT = SHIFT
    CONTROL = 'Control'
    LEFT_CONTROL = CONTROL
    ALT = 'Alt'
    LEFT_ALT = ALT
    # PAUSE = '\ue00b'
    ESCAPE = 'Escape'
    # SPACE = '\ue00d'
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
    # SEMICOLON = '\ue018'
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
    # MULTIPLY = '\ue024'
    # ADD = '\ue025'
    # SEPARATOR = '\ue026'
    # SUBTRACT = '\ue027'
    # DECIMAL = '\ue028'
    # DIVIDE = '\ue029'

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
    # COMMAND = '\ue03d'
    # ZENKAKU_HANKAKU = '\ue040'


class Interceptor(type):

    def __getattribute__(cls, item):
        if DriverWrapper.is_selenium:
            return getattr(SeleniumKeys, item)
        return getattr(PlaywrightKeys, item, NotImplementedError('Key is not added to Mops framework'))


class KeyboardKeys(SeleniumKeys, PlaywrightKeys, metaclass=Interceptor):
    pass
