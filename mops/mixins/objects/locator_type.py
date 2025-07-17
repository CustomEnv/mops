class LocatorType:
    """
    A container for locator types.

    This class standardizes the locator types used in the Mops framework, ensuring
    consistency and clarity when locating elements within web pages.

    .. note::
        You can specify a locator type along with your locator using the following syntax:

        - :obj:`Element('xpath=//*[@class="class-name"]')`
        - :obj:`Element('css=[class *= class-name]')`
        - :obj:`Element('text=some text with spaces')`
        - :obj:`Element('id=id-without-spaces')`

        The same applies to the :class:`.Locator` object:

        - :obj:`Element(Locator(ios='xpath=//*[@class, "ios-specific"]'))`

    .. note::
        For better readability, you can use this class with the following syntax:

        - :obj:`Element(f'{LocatorType.XPATH}=//*[@class="class-name"]')`
        - :obj:`Element(f'{LocatorType.ANDROID_UIAUTOMATOR}=//*[@class="class-name"]')`
    """
    CSS: str = 'css'
    XPATH: str = 'xpath'
    ID: str = 'id'
    TEXT: str = 'text'

    # Appium mobile native context
    IOS_PREDICATE: str = '-ios predicate string'
    IOS_UIAUTOMATION: str = '-ios uiautomation'
    IOS_CLASS_CHAIN: str = '-ios class chain'
    ANDROID_UIAUTOMATOR: str = '-android uiautomator'
    ANDROID_VIEWTAG: str = '-android viewtag'
    ANDROID_DATA_MATCHER: str = '-android datamatcher'
    ANDROID_VIEW_MATCHER: str = '-android viewmatcher'
    WINDOWS_UI_AUTOMATION: str = '-windows uiautomation'
    ACCESSIBILITY_ID: str = 'accessibility id'
    IMAGE: str = '-image'
    CUSTOM: str = '-custom'
