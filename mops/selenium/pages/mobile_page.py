from __future__ import annotations

from abc import ABC
import time

from mops.selenium.core.core_page import CorePage


class MobilePage(CorePage, ABC):

    def swipe(
            self,
            start_x: int,
            start_y: int,
            end_x: int,
            end_y: int,
            duration: int = 0,
            sleep: float = 0,
    ) -> MobilePage:
        """
        Appium only: Swipe from one point to another, with an optional duration and post-swipe delay.

        :param start_x: The x-coordinate at which to start the swipe.
        :type start_x: int
        :param start_y: The y-coordinate at which to start the swipe.
        :type start_y: int
        :param end_x: The x-coordinate at which to end the swipe.
        :type end_x: int
        :param end_y: The y-coordinate at which to end the swipe.
        :type end_y: int
        :param duration: The duration of the swipe in milliseconds.
        :type duration: int
        :param sleep: The delay (in seconds) after completing the swipe.
        :type sleep: Union[int, float]
        :return: :obj:`MobilePage` - The current instance of the page object.
        """
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)
        time.sleep(sleep)
        return self

    def swipe_down(self) -> MobilePage:
        """
        Scroll the page downward using a swipe gesture.

        :return: :obj:`MobilePage` - The current instance of the page object.
        """
        self.swipe(0, 500, 0, 100, sleep=0.1)
        return self

    def swipe_up(self) -> MobilePage:
        """
        Scroll the page upward using a swipe gesture.

        :return: :obj:`MobilePage` - The current instance of the page object.
        """
        self.swipe(0, 100, 0, 500, sleep=0.1)
        return self
