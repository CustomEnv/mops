# Element Key Features

```{note}
Here you will find information on complex or ambiguous functionality.
For a comprehensive list of all available methods, 
please refer to the {doc}`Element Interface <./interface>` documentation.
```

<br>

## 1. Delayed Element initialization:

```{important}
Following information suitable for `Element` object, that defined as class attribute of `Page` or `Group`
```

**Key functionality:**
- Elements are initialized based on the current driver. If no driver is available, the element will be initialized later within the `Page` or `Group` class initialisation.
- The `driver` and `driver_wrapper` will sets to `Element` object automatically from `Page` or `Group` instances


---

<br>

## 2. Custom waits
The waiting methods for _Selenium_ and _Appium_ have been reworked to improve efficiency, 
particularly for negative checks (i.e., when an element is not present on the page).

**Key changes:**
- Reduced `implicitly_wait`: The default implicitly_wait time in _Selenium_ and _Appium_ has been reduced. This adjustment is made because Selenium's `implicitly_wait` tends to cause long delays when checking for elements that are not present on the page.
- Internal Waiting Mechanism: Instead of relying on _Selenium's_ or _Appium's_ native waiting strategies, all waiting methods now use internal methods with built-in Python loops. This allows for more precise control over the waiting time and conditions, leading to faster and more reliable checks.

---

<br>


## 3. Built-in waits
Most methods automatically wait for specific element states.
For example, the framework will wait until a web element becomes clickable before executing `click` method on it.

---

<br>


## 4. Original locator preservation
The `source_locator` attribute stores the original locator exactly as it was provided to `Element.__init__`,
before any platform-specific resolution or framework-specific transformations.

```{note}
For **static** sub-elements, consider using the built-in parent mechanism instead —
`Element` objects defined as class attributes of a `Group` automatically search within
the Group locator (see {doc}`Group documentation <../group_object/index>`).

`source_locator` is designed for cases where you need the **raw locator string** for
dynamic XPath construction at runtime — something the parent mechanism cannot do.
```

**Example — dynamic table parsing:**

```python
from mops.base.group import Group
from mops.base.element import Element


class DataTable(Group):

    def load(self):
        row_locator = f'{self.source_locator}//tr'
        row_elements = Element(row_locator, f'{self.name}: Rows').all_elements

        self.rows = []
        for index, _ in enumerate(row_elements):
            cell_locator = f'({row_locator})[{index + 1}]/td'
            cells = Element(cell_locator, f'{self.name}: Row {index} cells')
            self.rows.append(cells)
```

Here `source_locator` is used to dynamically compose new XPath expressions
via string concatenation. This cannot be achieved with the parent mechanism because:

- The XPath grouping operator `(…)[n]` requires building the full expression as a single string.
- New `Element` objects are created at runtime, not as class-level attributes.
- After initialization, `locator` is transformed with platform prefixes
  (e.g., `xpath=` for Playwright), making it unsuitable for string concatenation.

```{note}
`source_locator` preserves the exact type passed in: if a `Locator` dataclass was given, it stays a `Locator`;
if a string was given, it stays the original string.
The `locator` attribute, by contrast, is resolved to a platform-specific string and may be further modified
(e.g., prefixed with `xpath=` for Playwright or converted to a CSS selector for ID-based locators in Selenium).
```
