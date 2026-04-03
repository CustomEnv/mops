# Getting Started

<br>

To get started with <Mops>, follow these steps:

## 1. Installation
Install Mops via pip:

```bash
pip3 install mops
```

---

## 2. Write Simple Page Object

<br>

```{note}
For the PageObject example, the [UI Automation Playground](https://customenv.github.io/test-automation-playground/) site is used.
``` 

```python
from mops.base.element import Element
from mops.base.group import Group
from mops.base.page import Page


class Card(Group):
    view_page_button = Element('//a[.="View Page"]', name='view page button')

    def click_view_page_button(self):
        self.view_page_button.click()


class BasicControlsSection(Group):

    def __init__(self):
        super().__init__('//*[contains(@class, "card") and .//*[.="Basic Form Controls"]]', name='For page')

    python_checkbox = Element('check_python', name='python checkbox')
    checkbox_label = Element('check_validate', name='checkbox label')


class FormsPage(Page):

    def __init__(self):
        super().__init__('.container', name='Forms page')

    controls_section = BasicControlsSection()


class MainPage(Page):
    def __init__(self):
        super().__init__('//h1[.="The Playground"]', name='Playground page')

    frames_card = Card('//*[contains(@class, "card") and  contains(., "Frames")]', name='frames card')

    def navigate_to_frames_page(self) -> FormsPage:
        self.frames_card.click_view_page()
        return FormsPage()
```

---

## 3. Set Up The Driver

<br>

### Selenium driver setup

```python
import pytest  # noqa
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver

from mops.base.driver_wrapper import DriverWrapper
from mops.mixins.objects.driver import Driver


@pytest.fixture
def driver_wrapper():
    selenium_driver = Driver(driver=ChromeWebDriver())
    return DriverWrapper(selenium_driver)
```

---

<br>

### Appium driver setup

```python
import pytest  # noqa
from appium.webdriver.webdriver import WebDriver as SourceAppiumDriver
from appium.options.common.base import AppiumOptions

from mops.base.driver_wrapper import DriverWrapper
from mops.mixins.objects.driver import Driver


@pytest.fixture
def driver_wrapper():
    caps = {}  # Your device capabilities
    appium_ip, appium_port = None, None  # Your appium ip and port
    options = AppiumOptions().load_capabilities(caps)

    appium_driver = SourceAppiumDriver(
        command_executor=f'http://{appium_ip}:{appium_port}/wd/hub',
        options=options
    )

    return DriverWrapper(Driver(driver=appium_driver))
```

---

<br>

### Playwright driver setup

```{attention}
Mops supports only sync API of playwright
```

```python
import pytest  # noqa
from playwright.sync_api import sync_playwright
from mops.mixins.objects.driver import Driver

from mops.base.driver_wrapper import DriverWrapper


@pytest.fixture
def driver_wrapper():
    instance = sync_playwright().start().chromium.launch()
    context = instance.new_context()
    page = context.new_page()

    return DriverWrapper(Driver(driver=page, context=context, instance=instance))
```

---

## 4. Write A Test

<br>

```python
from ... import MainPage  # noqa


# pytest function
def test_example(driver_wrapper):
    driver_wrapper.get("https://customenv.github.io/test-automation-playground/")
    forms_page = MainPage().navigate_to_frames_page()
    
    assert forms_page.is_page_opened(), 'Forms Page is not opened after navigation'
    assert not forms_page.controls_section.checkbox_label.is_visible(), 'Checkbox label unexpectedly visible'
    
    forms_page.controls_section.python_checkbox.click()
    
    assert forms_page.controls_section.checkbox_label.text == 'PYTHON'
```

---

<br>

For detailed information, please refer to the next section of the documentation that addresses your questions
