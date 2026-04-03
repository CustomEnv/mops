# DriverWrapper

```{toctree}
---
hidden:
---

dw_interface
dws_interface
```

## Overview

The `DriverWrapper` module provides a unified interface to interact with different web and mobile automation frameworks,
such as _Selenium_, _Appium_, and _Playwright_. It abstracts the complexities of these frameworks and offers a seamless 
experience for managing driver sessions, performing operations, and handling cross-platform automation tasks.

<br>

### Core Benefits & Rules

1. **Centralized Session Management:**
   - The `DriverWrapperSessions` interface simplifies the management of driver sessions, offering a centralized way to handle multiple sessions throughout your testing process.

2. **Seamless Integration:**
   - The `DriverWrapper` and its underlying `Driver` instance are easily accessible within your `Page`, `Group`, and `Element` objects, allowing for consistent and efficient interactions across your test suite.

3. **Dynamic Status Attributes:**
   - `DriverWrapper` provides various status attributes (e.g., `is_mobile`, `is_selenium`, `is_playwright`, `is_cdp`) that help you tailor your test behavior based on the current driver environment, ensuring more precise control and adaptability in your tests.

4. **Optimal Driver Setup:**
   - The initialization of the source driver should be handled within your testing framework. This approach ensures that the browser or device starts with the most appropriate configuration, leading to more reliable and efficient test executions.

<br>

This section covers features and behaviour of `DriverWrapper` class detail:
- {doc}`DriverWrapper Interface <./dw_interface>`
- {doc}`DriverWrapperSessions Interface <./dws_interface>`