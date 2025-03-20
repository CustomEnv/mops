from mops.base.driver_wrapper import DriverWrapper
from tests.adata.pages.mouse_event_page import MouseEventPageV2
from tests.adata.pages.pizza_order_page import PizzaOrderPage


def test_second_driver_for_mobile_same_page(driver_wrapper, second_driver_wrapper):
    mouse_page_mobile = MouseEventPageV2(driver_wrapper)  # mobile driver
    mouse_page_desktop = MouseEventPageV2(second_driver_wrapper)  # desktop driver
    assert len(DriverWrapper.session.all_sessions) == 2

    mouse_page_mobile.open_page()
    mouse_page_desktop.open_page()

    assert mouse_page_desktop.is_page_opened()
    assert mouse_page_mobile.is_page_opened()


def test_second_driver_for_mobile_different_page(driver_wrapper, second_driver_wrapper):
    pizza_page = PizzaOrderPage(driver_wrapper)  # mobile driver
    mouse_page = MouseEventPageV2(second_driver_wrapper)  # desktop driver
    assert len(DriverWrapper.session.all_sessions) == 2

    mouse_page.open_page()
    pizza_page.open_page()

    assert pizza_page.driver_wrapper is not mouse_page.driver_wrapper
    assert pizza_page.driver is not mouse_page.driver
    assert mouse_page.header_logo.driver is not pizza_page.quantity_input.driver
    assert mouse_page.header_logo.driver_wrapper is not pizza_page.quantity_input.driver_wrapper

    assert mouse_page.is_page_opened()
    assert mouse_page.header_logo.is_displayed()

    assert pizza_page.is_page_opened()
    assert pizza_page.quantity_input.is_displayed()
