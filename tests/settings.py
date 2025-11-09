import os

domain_name = 'https://customenv.github.io'
automation_playground_repo_name = 'test-automation-playground'

appium_logs_path = '.venv/.tmp/logs/android_appium.txt'
android_device_start_timeout = 60

def get_android_desired_caps():
    env = os.environ

    return {
        'deviceName': env.get('ANDROID_DEVICE_NAME') or 'emulator-5555',
        'platformName': 'Android',
        'platformVersion': env.get('ANDROID_PLATFORM_VERSION') or '13.0',
        # Update following capabilities before driver init
        # 'app': 'https://testingbot.com/appium/sample.apk',
        # 'browserName': 'Chrome',
        'automationName': 'UiAutomator2',
        'autoDownloadChromeDriver': True,
        'noReset': True,
        'newCommandTimeout': 3000,
        'avdLaunchTimeout': 120000,
        'avdReadyTimeout': 120000,
        'adbExecTimeout': 120000,
    }

def get_ios_desired_caps():
    env = os.environ

    return {
        'deviceName': env.get('IOS_DEVICE_NAME') or 'iPhone 16',
        'platformVersion': env.get('IOS_PLATFORM_VERSION') or '18.6',
        'udid': env.get('udid') or '',
        'automationName': 'XCUITest',
        'platformName': 'iOS',
        'browserName': 'Safari',
        'newCommandTimeout': 3000,
        'wdaLaunchTimeout': 120000,
        'autoWebview': True,
    }
