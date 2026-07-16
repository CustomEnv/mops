<p align="center">
  <a href="https://mops.readthedocs.io"><img src="https://raw.githubusercontent.com/CustomEnv/mops/master/docs/source/_static/preview.png"></a>
</p>

<h2 align="center">Automation Beyond Limits</h2>

<p align="center">
    <a href="https://github.com/CustomEnv/mops/blob/master/LICENSE"><img alt="GitHub License" src="https://img.shields.io/github/license/CustomEnv/mops?logo=github&color=%234F2684&labelColor=%232E353B"></a>
    <a href="https://pypi.org/project/mops/"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/mops?logo=pypi&labelColor=%232E353B"></a>
    <a href="https://pypi.org/project/mops/"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/mops?logo=pypi&labelColor=%232E353B"></a>
</p> 

<p align="center">
    <a href="https://mops.readthedocs.io"><img alt="Documentation Status" src="https://readthedocs.org/projects/mops/badge/?version=latest"></a>
    <a href="https://github.com/CustomEnv/mops/actions/workflows/static_tests.yml"><img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/CustomEnv/mops/static_tests.yml?branch=master&logo=github&label=Unit%20Tests&labelColor=%232E353B"></a>
    <a href="https://github.com/CustomEnv/mops/actions/workflows/playwright_tests.yml"><img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/CustomEnv/mops/playwright_tests.yml?branch=master&logo=github&label=Playwright%20Tests&labelColor=%232E353B"></a>
</p> 

<p align="center">
    <a href="https://github.com/CustomEnv/mops/actions/workflows/selenium_tests.yml"><img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/CustomEnv/mops/selenium_tests.yml?branch=master&logo=github&label=Selenium%20Tests&labelColor=%232E353B"></a>
    <a href="https://github.com/CustomEnv/mops/actions/workflows/selenium_safari_tests.yml"><img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/CustomEnv/mops/selenium_safari_tests.yml?branch=master&logo=github&label=Selenium%20Safari%20Tests&labelColor=%232E353B"></a>
    <a href="https://github.com/CustomEnv/mops/actions/workflows/appium_android_tests.yml"><img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/CustomEnv/mops/appium_android_tests.yml?branch=master&logo=github&label=Android%20Tests&labelColor=%232E353B"></a>
    <a href="https://github.com/CustomEnv/mops/actions/workflows/appium_ios_tests.yml"><img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/CustomEnv/mops/appium_ios_tests.yml?branch=master&logo=github&label=iOS%20Tests&labelColor=%232E353B"></a>
</p>


> [!NOTE]
> Previously known as [dyatel-wrapper](https://github.com/CustomEnv/dyatel-wrapper). 
> This project follows the versioning of `dyatel-wrapper`.


Mops is a Python framework that seamlessly wraps over Selenium, Appium, and sync Playwright,
providing a unified interface for browser and mobile automation. With Mops, you can effortlessly switch 
between these engines within the same test, allowing you to leverage the unique features of each framework without boundaries.

Whether you're running tests on web browsers, mobile devices, or a combination of both, Mops simplifies the 
process, giving you the flexibility and power to automate complex testing scenarios with ease.

## Key Features

- **Seamless Integration**: Mops integrates with Selenium, Appium, and Playwright, allowing you to use the best-suited engine for your specific testing needs.
- **Unified API**: A single, easy-to-use API that abstracts away the differences between Selenium, Appium, and Playwright, making your test scripts more readable and maintainable.
- **Engine Switching**: Switch between Selenium, Appium, and Playwright within the same test case, enabling cross-platform and cross-browser testing with minimal effort.
- **Visual Regression Testing**: Perform visual regression tests using the integrated visual regression tool, available across all supported frameworks. This ensures your UI remains consistent across different browsers and devices.
- **Advanced Features**: Leverage the advanced features of each framework, such as Playwright's mocks and Appium's real mobile devices support, all while using the same testing framework.
- **Extensibility**: Extend the framework with custom functionality tailored to your project's specific requirements.
- **Automatic Locator Type Definition**: The locator type will be automatically determined based on the provided locator string or `Locator` object.


## Installation and usage
For information on installation and usage, please refer to our **[ReadTheDocs documentation](https://mops.readthedocs.io)**. Check it out for more details.

## Contributing

Mops is an open-source project, and we welcome contributions from the community. If you'd like to contribute, please open an pull request from your fork

## License

Mops is licensed under the Apache License. See the [LICENSE](https://github.com/CustomEnv/mops/blob/master/LICENSE) file for more details.

## Support

If you encounter any issues or have questions, please feel free to reach out via our [GitHub Issues](https://github.com/CustomEnv/mops/issues) page.

Thank you for choosing Mops for your automation needs!
