# Mops Changelog

<br>

## Patch: v3.1.1, v3.2.1 
*Release date: 2025-07-18*

### Added
- Appium related locator types in `LocatorType` class

### Changed
- Selenium only: `DriverWrapper.set_window_size` inner viewport calculation skipped for mobile resolution

### Removed
- Automatic locator type detection for text based locators 

### Fixed
- Visual comparison dummy element class name
- Visual comparison error traceback

---

## v3.2.0
*Release date: 2025-03-31*

### Added
- Continuous verification waits for `Element.wait_visibility` and `Element.wait_hidden`
- `ContinuousWaitException` for continuous verification errors in wait methods
- Caret hiding for screenshots in Selenium / Appium
- `is_displayed` / `is_hidden` execution results logged
- Retry decorator for Selenium / Appium methods to handle `StaleElementReferenceException`

### Changed
- Playwright's `wait_visibility`, `wait_hidden`, and `wait_availability` logic moved to MOPS methods

### Fixed
- Small bug in the documentation example
- Bug in the `assert_screenshot` method with the `remove` argument for certain popups
- `StaleElementReferenceException` handler during wait/gathering of `Element.text`

---

## v3.1.0
*Release date: 2025-01-29*

### Added
- [Kitchen Sink](https://mops.readthedocs.io/3.1.0/kitchen_sink/index.html) section on ReadTheDocs
- Source code links for interfaces in ReadTheDocs [< example > ](https://mops.readthedocs.io/3.1.0/_modules/mops/base/driver_wrapper.html#DriverWrapper.save_screenshot)
- `PlayDriver.delete_cookie` method
- `PlayDriver.switch_to_frame` method
- `PlayDriver.switch_to_default_content` method
- `LocatorType` constants [< more info >](https://mops.readthedocs.io/3.1.0/kitchen_sink/locator_type.html)

### Changed
- **Breaking:** Minimum Playwright version is now [1.48.0](https://pypi.org/project/playwright/1.48.0/)
- **Breaking:** `DriverWrapper.get_inner_window_size` now returns a `Size` object instead of a `tuple`
- **Breaking:** `DriverWrapper.set_window_size` now sets the inner window size (affects Selenium only)
- **Breaking:** `Box.get_image_cut_box` now accepts a `Size` object for the `size` argument and returns a `Box` object
- `PlayDriver.get_inner_window_size` now retrieves `page.viewport_size` instead of using a custom JavaScript script
- Improved error logging for `Element`: Selector output has been adjusted
- `Element` representation: `locator_type` is now part of `locator`
- Reduced exception inheritance in `VisualComparison`
- Selenium & Appium error logging
- Improved most docstrings

### Fixed
- `Element.wait_for_value` now correctly handles an empty `expected_value` argument
- `Element.wait_for_text` now correctly handles an empty `expected_text` argument
- `Element.value` now returns an empty string instead of `None`

### Removed
- **Breaking:** Removed `Locator.loc_type` attribute/argument [< how to provide locator type >](https://mops.readthedocs.io/3.1.0/kitchen_sink/locator_type.html)
- **Breaking:** Removed `CutBox` dataclass [< use Box instead >](https://mops.readthedocs.io/3.1.0/kitchen_sink/box.html)

### Reworked
- Unified selector synchronization methods across all frameworks
- Improved automatic locator type detection

---

## v3.0.0  
*Release date: 2025-01-13*

### Breaking: Project renamed

### Changed 
- Dev: pyproject.toml integrated instead of setup.py
- Dev: UV integrated

### Removed
- Dev: tox usage removed

---

## v2.4.0  
*Release date: 2025-01-10*

### Added  
- `DriverWrapper.is_safari` method
- `DriverWrapper.is_firefox` method
- `DriverWrapper.is_chrome` method
- `InvalidLocatorException` for locator validation
- `VisualComparison` now removes actual and diff files upon successful assertions
- Internal CI pipelines with tests

### Removed  
- `DriverWrapper.switch_to_parent_frame` method
- `dyatel/dyatel_play/helpers/trace.py` module

### Changed  
- `DriverWrapper.get_inner_window_size` now returns a `Size` object instead of a dictionary
- `Element.click` now uses a JavaScript click for the Safari driver
- `Element.click_outside` now has default arguments `x=-5, y=-5` across all platforms
- `VisualComparison` dummy elements' `style.position` changed from `"fixed"` to `"absolute"`
- `VisualComparison` dummy elements' `style.top/left` now account for page scroll
- `VisualComparison` now includes a `sleep(0.1)` delay if `fill_background` or `remove` actions are specified after an action
- The Safari browser on Appium and Selenium uses the `innerText` DOM property instead of the driver's `text` API to improve compatibility with other platforms
- The Safari browser on Selenium uses JavaScript-based `click` instead of the driver's `click` API to enhance compatibility with other platforms
- Documentation for most methods has been improved

### Fixed  
- `DriverWrapper.save_screenshot` no longer throws an error when called without the optional `screenshot_base` argument
- `Element.save_screenshot` no longer throws an error when called without the optional `screenshot_base` argument
- `VisualComparison.assert_screenshot` with the argument `threshold=0` now respects the provided value instead of defaulting
- `VisualComparison` under `soft_generate_reference` no longer takes two images (actual → assertion → reference)

---

## v2.3.3
*Release date: 2025-01-09*

### Added
- `dyatel.mixins/objects.driver.Driver` object

### Changed
- **Breaking:** `DriverWrapper` initialization now requires a `Driver` object
- **Breaking:** Playwright's `context` and `page` creation have been moved out of `dyatel-wrapper`

**Note:** Examples of the new logic can be found in the [ReadTheDocs documentation](https://dyatel-wrapper.readthedocs.io/getting_started.html#selenium-driver-setup)

---

## v2.3.2
*Release date: 2024-12-19*

### Changed
- Supported Python-Appium-Client version changed from `2.11.1` to `3.1.0`
- Supported appium version changed from `2.2.1` to `2.12.1`
- Supported xcuitest version changed from `5.0.0` to `7.28.3`
- Supported uiautomator2 version changed from `2.34.1` to `3.9.0`

---

## v2.3.1
*Release date: 2024-12-16*

### Fixed
- Memory leak due to misuse of lru_cache

---

## v2.3.0
*Release date: 2024-09-12*

### Added
- [ReadTheDocs documentation](https://dyatel-wrapper.readthedocs.io/)
- `Locator` object
- `CutBox` object
- `tablet` locator support
- `ScrollTo` & `ScrollTypes` constants
- `VisualComparison.assert_screenshot` now supports the use of the `CutBox` object
- `Element.execute_script` method, which automatically sets itself to script arguments
- Selenium only: 0.1 seconds delay between requests for all waiting methods
- Playwright only: 0.1 seconds delay between requests for a few waiting methods
- Appium only: exponential delay starting at 0.1 seconds between requests for all waiting methods

### Changed
- **Breaking:** `locator_type`, `mobile`, `ios`, `android`, and `desktop` kwargs removed
- **Breaking:** Most `Element` methods have been renamed
- **Breaking:** `DriverWrapper.execute_script` now uses the `Element` object instead of the source element object
- **Breaking:** `MobileDriver.get_top_bar_height` method renamed to the `top_bar_height` property 
- **Breaking:** `MobileDriver.get_bottom_bar_height` method renamed to the `bottom_bar_height` property 
- `Element.scroll_into_view` method now uses `ScrollTo` & `ScrollTypes` constants
- Default timeout for `Element.wait_hidden_without_error` reduced to 2.5 seconds since it's a negative wait
- Default timeout for `Element.wait_visibility_without_error` reduced to 2.5 seconds since it's a negative wait
- Selenium & Appium only: `Element.click` now retries on `ElementNotInteractableException`, `ElementClickInterceptedException`, `StaleElementReferenceException` exceptions
- Automatically generated `name` argument, based on the attribute name, has been removed

### Fixed
- Playwright: Appending of dummy elements inside `Element.assert_screenshot`
- Playwright: `DriverWrapper.execute_script` error when multiple elements are available

### Reworked
- Mobile `top_bar_height` and `bottom_bar_height` now use `NativeContext` & `NativeSafari` objects
- Most `Element` `wait` methods are now resolved with the `wait_condition` decorator

---

## v2.2.15
*Release date: 2024-08-13*

### Added  
- Python 3.11 and 3.12 support

---

## v2.2.14
*Release date: 2024-07-24*

### Added  
- assert_screenshot: possibility to hide objects before taking screenshot
- assert_screenshot: the diff image save on a different sized screenshots (reference/output)
- assert_screenshot: allure attachments increased for some cases 
- assert_screenshot: auto label `mobile` for mobile resolution screenshots

### Fixed
- assert_screenshot: bug with default.png for screenshots with given names fixed

---

## v2.2.12 & v2.2.13
*Release date: 2024-06-08*

### Added  
- iPad support 

---

## v2.2.11
*Release date: 2024-05-29*

### Changed 
- Minimum playwright version is 1.41.0

---

## v2.2.1
*Release date: 2024-04-16*

### Added 
- `DriverWrapper.is_tablet`
- `DriverWrapper.is_appium` 
- `DriverWrapper.is_ios_tablet` 
- `DriverWrapper.is_ios_mobile` 
- `DriverWrapper.is_android_tablet` 
- `DriverWrapper.is_android_mobile` 

### Fixed
- `Element.is_fully_visible` calculation 
- `Element.is_visible` calculation 

---

## v2.2.0
*Release date: 2024-03-04*

### Added
- `Element.size` method
- `Element.location` method
- `Element.wait_element_size` method
- `DriverWrapper.assert_screenshot` method
- `DriverWrapper.soft_assert_screenshot` method
- `DriverWrapper.wait` method
- `DriverWrapper/Element.screenshot_image` method

### Changed 
- `DriverWrapper/Element.screenshot_base` method now return image binary
- `DriverWrapper/Element.save_screenshot` method now saves screenshot and moved to base class
- iOS only: `DriverWrapper.screenshot_base` returns image binary without native controls
- iOS only: `Element.screenshot_base` screenshot size for some elements could be changed


### Fixed 
- Type annotations
- `Element.is_visible/is_fully_visible` calculation
- iOS only: `Element.get_bottom_bar_height` calculation

---

## v2.1.9
*Release date: 2024-02-22*

### Added
- Playwright `context.tracing` support

---

## v2.1.8
*Release date: 2024-01-04*

### Added
- Playwright `new_context` args supports

---

## v2.1.7
*Release date: 2023-12-05*

### Added
- VisualComparison: Dynamic threshold calculation

---

## v2.1.6
*Release date: 2023-11-26*

### Fixed
- Performance fixes for session with 2 or more browser windows

---

## v2.1.5
*Release date: 2023-10-17*

### Fixed
- Typo fix inside `MobileDriver`

---

## v2.1.4
*Release date: 2023-10-16*

### Fixed
- Internal usage of Element class inside DriverWrapper

### Changed
- AssertionError output of visual comparison

### Added
- Soft visual reference generation
- Soft assert screenshot
- `LogLevel` class

---

## v2.1.3
*Release date: 2023-09-10*

### Changed
- Selenium/Appium only: Additional logging for element enabled
- Selenium/Appium element gathering and exceptions reworked

---

## v2.1.2
*Release date: 2023-09-07*

### Fixed
- Additional logging for element disabled 

---

## v2.1.1
*Release date: 2023-09-07*

### Fixed
- `setup.py` packages 

---

## v2.1.0
*Release date: 2023-09-07*

### Added
- Abstract classes and methods
- `DriverWrapperSessions` class
- `DriverWrapper.browser_name` attribute
- Inheritance validation
- `Element.scroll_into_view` 'block' argument validation
- Selenium/Appium only: additional warning for `element` errors 

### Fixed
- Type annotations for some methods

### Changed
- `Page.anchor` property now instance attribute
- Some methods moved to subclasses
- Internal `Logging` reworked
- `DriverWrapper` from previous object reworked

---

## v2.0.0
*Release date: 2023-04-06*

### Added
- `element.wait_enabled` method
- `element.wait_disabled` method
- `element.is_enabled` method
- `VisualComparison.default_delay` property
- `VisualComparison.default_threshold` property
- `DriverWrapper.switch_to_alert` method (Selenium Only)
- `DriverWrapper.accept_alert` method (Selenium Only)
- `DriverWrapper.dismiss_alert` method (Selenium Only)
- `MobileDriver.click_in_alert` method (Appium Only)

### Fixed
- MRO for Mobile + Desktop session
- Rapidly requests for current context on mobile
- `element.all_elements` recursion
- logging stderr to stdout

### Changed
- Checkbox class removed (all methods in Element class)
- New screenshot comparison engine. By: [@laruss](https://github.com/laruss)
- Elements initialization
- `element.wait_clickable` renamed to `element.wait_enabled`
- `__repr__` for Element/Group/Page
- Driver with index will be added to logs always

---

## v1.3.4
*Release date: 2023-01-17*

### Fixed
- Error logs fixes

---

## v1.3.3
*Release date: 2023-01-12*

### Changed
- `element.assert_screenshot` elements removal rework

---

## v1.3.2
*Release date: 2022-12-08*

### Added
- mobile `element.hide_keyboard` method added
- `fill_background` arg in `element.assert_screenshot`

### Changed
- ios safaridriver support removed
- reruns disabling for visual tests without references

### Fixed
- Pillow warning fixes
- other fixes and improvements

---

## v1.3.1
*Release date: 2022-12-02*

### Added
- `element.wait_element_hidden_without_error` method
- `element.assert_screenshot` hard reference generation support
- `element.assert_screenshot` soft reference generation fix
- `element.hover` silent argument

### Changed
- Reworked wait argument for `element`: False - wait element hidden; True - wait element visible
- `page.is_page_opened` without url support
- selenium - tags (locator type) updated

### Fixed
- DifferentDriverWrapper and elements initialization fixes

---

## v1.3.0
*Release date: 2022-10-18*

### Added 
- `driver_wrapper.get_inner_window_size` method
- `driver_wrapper.switch_to_frame` method for selenium based driver
- `driver_wrapper.switch_to_parent_frame` method for selenium based driver
- `driver_wrapper.switch_to_default_content` method for selenium based driver
- `driver_wrapper.delete_cookie` method for selenium/appium based driver
- `element.is_visible` method 
- `element.is_fully_visible` method
- `element.__repr__`, `checkbox.__repr__`, `group.__repr__`, `page.__repr__` 
- `scroll_into_view` before `element.click_into_center/hover/etc.` if element isn't visible
- `name_suffix` arg for `element.assert_screenshot` 
- Auto implemented `driver` in hidden object (function/property etc.) for `element/checkbox/group/page`
- Auto implemented `parent` in hidden object (function/property etc.) for `element/checkbox`
- Platform specific locator by object kwargs: ios/android/mobile/desktop

### Changed
- `element.get_rect` for selenium desktop
- All visual comparisons staff moved to `VisualComparison` class 
- Logging

### Fixed
- `get_object_kwargs` function
- `initialize_objects_with_args` function
- `element.assert_screenshot` driver name for remote
- Click by location after scroll

---

## v1.2.8
*Release date: 2022-09-20*

### Added 
- `driver_wrapper.is_native_context` property on mobile
- `driver_wrapper.is_web_context` property on mobile
- `driver_wrapper.visual_reference_generation` that disable AssertionError exception in `element.assert_screenshot`
- `ElementNotInteractableException` handler in `element.click`

### Changed
- `element.get_rect` output value sorting
- `PlayDriver`/`CoreDriver` class variables moved to `DriverWrapper`
- `os.environ['visual']` changed to `driver_wrapper.visual_regression_path`
- `element.wait_element` exception message
- Mobile: Finding elements in native context now skips parent

### Fixed
- `autolog` params
- `driver_wrapper.switch_to_tab` with default params

---

## v1.2.6/7
*Release date: 2022-09-15*

### Fixed
- screenshot name generation

---

## v1.2.5
*Release date: 2022-09-13*

### Added
- `element.click_into_center` method
- `driver_wrapper.click_by_coordinates` method

### Fixed
- `calculate_coordinate_to_click` calculation
- Shared object of groups become unique for each class

---

## v1.2.4
*Release date: 2022-09-08*

### Added
- `assert_screenshot()` elements removal

---

## v1.2.3
*Release date: 2022-09-02*

### Fixed
- `element.is_displayed()` exception handler

---

## v1.2.1/2
*Release date: 2022-08-31*

### Fixed
- Annotations

---

## v1.2.0
*Release date: 2022-08-31*

### Added
- [Allure Screen Diff Plugin](https://github.com/allure-framework/allure2/blob/master/plugins/screen-diff-plugin/README.md) support
- Driver specific logs 
- Custom exceptions
- Screenshot name generation in `assert_screenshot`
- `KeyboardKeys` class
- `element.send_keyboard_action` method

### Changed
- `get_text` property become `text`
- `get_value` property become `value`
- `get_screenshot_base` property become `screenshot_base`
- `get_inner_text` property become `inner_text`
- `by_attr` arg of `Checkbox` removed
- `calculate_coordinate_to_click` now calculate coordinates from element location

### Fixed
- Reduced count of `find_element` execution
- Page `driver_wrapper` getter exception

---

## v1.1.1
*Release date: 2022-08-10*

### Added
- iOS SafariDriver basic support 
- Different second driver support (for mobile/desktop safari)
- Tabs manipulating methods for desktop in `CoreDriver/PlayDriver`
- Context manipulating methods for mobile in `MobileDriver`
- [pytest-rerunfailures](https://pypi.org/project/pytest-rerunfailures/#pytest-rerunfailures) support
- Type annotations for most of code
- Auto `locator_type` support for `com.android` locator 
- `element.hover` support on mobiles
- `element.hover_outside` method, that moves pointer outside from current position
- `page.swipe(_up/_down)` methods for mobile  
- Default cookie path/domain in `driver_wrapper.set_cookie` method

### Changed
- `Driver` becomes `DriverWrapper` for more readability
- Mixins classes renamed and moved to `dyatel.mixins` folder
- Selenium `core_element.wait_element` now using `is_displayed`
- Selenium exception stacktrace reduced in most cases

### Fixed
- Custom `driver_wrapper`/`driver` for child elements
- Selenium `KeyError` of `driver_wrapper.set_cookie` without `domain` 
- Driver creation with function scope of pytest

---

## v1.1.0
*Release date: 2022-07-23*

### Added
- `Checkbox` class for Playwright and Selenium 
- `set_text` method in `Element` class
- `wait_elements_count` method in `Element` class
- `wait_element_text` method in `Element` class
- `wait_element_value` method in `Element` class
- `driver_wrapper` arg for `Group` and `Page`

### Changed
- Page/Group `set_driver` workflow
- `CorePage` and `PlayPage` methods moved to `Page` 

---

## v1.0.5
*Release date: 2022-07-10*

### Added
- `_first_element` property in `PlayElement`

### Changed
- `element` property replaced with `_first_element` for elements interactions
- `parent` nesting of `Element` changed from one level to endless
- `PlayElement` / `CoreElement` initialization

### Fixed
- `all_elements` execution time/nesting

---

## v1.0.4
*Release date: 2022-07-07*

### Added
- `set_driver` function for page object
- Multiple drivers support

### Changed
- Drivers initialization
- `driver`, `driver_wrapper` become property methods
