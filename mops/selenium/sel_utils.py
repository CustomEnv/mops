from __future__ import annotations

from selenium.webdriver import ActionChains as SeleniumActionChains


class ActionChains(SeleniumActionChains):

    def move_to_location(self, x: int, y: int) -> ActionChains:
        """
        Moving the mouse to specified location.

        :param x: x coordinate
        :param y: y coordinate
        :return: self
        """
        self.w3c_actions.pointer_action.move_to_location(x, y)
        self.w3c_actions.key_action.pause()

        return self
