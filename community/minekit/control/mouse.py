"""Mouse helpers for Minecraft actions."""

from __future__ import annotations

import time

import minescript

from ..game.timing import wait_ticks
from ..internal.enums import MouseButton

_BUTTON_TO_FUNCTION = {
    MouseButton.LEFT: minescript.player_press_attack,
    MouseButton.RIGHT: minescript.player_press_use,
    MouseButton.MIDDLE: minescript.player_press_pick_item,
}


class MouseController:
    """Thin wrapper around Minecraft mouse-like actions."""

    def __init__(self, *, sleep_fn=time.sleep):
        """Create a mouse controller.

        Args:
            sleep_fn: Delay function used between button down and up calls.
        """
        self._sleep = sleep_fn

    def _delay(self, delay: float):
        if delay > 0:
            self._sleep(delay)

    def _wait_ticks(self, ticks: int):
        if ticks > 0:
            wait_ticks(ticks)

    def down(self, button: MouseButton, delay: float = 0.0, delay_ticks: int = 0):
        """Press a Minecraft mouse button action without releasing it.

        Args:
            button: Which logical mouse button to press.
            delay: Optional delay after the press.
            delay_ticks: Optional delay after the press, measured in Minecraft ticks.
        """
        _BUTTON_TO_FUNCTION[MouseButton(button)](True)
        self._wait_ticks(delay_ticks)
        self._delay(delay)

    def up(self, button: MouseButton, delay: float = 0.0, delay_ticks: int = 0):
        """Release a Minecraft mouse button action.

        Args:
            button: Which logical mouse button to release.
            delay: Optional delay after the release.
            delay_ticks: Optional delay after the release, measured in Minecraft ticks.
        """
        _BUTTON_TO_FUNCTION[MouseButton(button)](False)
        self._wait_ticks(delay_ticks)
        self._delay(delay)

    def click(
        self,
        button: MouseButton,
        duration: float = 0.05,
        delay: float = 0.0,
        *,
        duration_ticks: int = 0,
        delay_ticks: int = 0,
    ):
        """Press and release a Minecraft mouse button action.

        Args:
            button: Which logical mouse button to trigger.
            duration: How long the button stays pressed.
            delay: Optional delay after the click finishes.
            duration_ticks: How many Minecraft ticks to hold the button before releasing it.
            delay_ticks: Optional delay after the click finishes, measured in Minecraft ticks.
        """
        button = MouseButton(button)
        self.down(button)
        self._wait_ticks(duration_ticks)
        if duration_ticks <= 0:
            self._sleep(duration)
        self.up(button)
        self._wait_ticks(delay_ticks)
        self._delay(delay)

    def spam(
        self,
        button: MouseButton,
        count: int,
        press_time: float = 0.05,
        interval: float = 0.03,
        delay: float = 0.0,
        *,
        press_ticks: int = 0,
        interval_ticks: int = 0,
        delay_ticks: int = 0,
    ):
        """Repeat a mouse click action multiple times.

        Args:
            button: Which logical mouse button to click.
            count: Number of click cycles to execute.
            press_time: How long each click stays pressed.
            interval: Delay between clicks.
            delay: Optional delay after the full spam sequence.
            press_ticks: How many Minecraft ticks each click stays pressed.
            interval_ticks: Delay between clicks, measured in Minecraft ticks.
            delay_ticks: Optional delay after the full spam sequence, measured in ticks.
        """
        if count < 0:
            raise ValueError("count must be >= 0")
        for index in range(count):
            self.click(button, duration=press_time, duration_ticks=press_ticks)
            if index + 1 < count and interval_ticks > 0:
                self._wait_ticks(interval_ticks)
            elif index + 1 < count and interval > 0:
                self._sleep(interval)
        self._wait_ticks(delay_ticks)
        self._delay(delay)

    def left_click(
        self,
        duration: float = 0.05,
        delay: float = 0.0,
        *,
        duration_ticks: int = 0,
        delay_ticks: int = 0,
    ):
        """Shortcut for ``click(MouseButton.LEFT, ...)``."""
        self.click(
            MouseButton.LEFT,
            duration=duration,
            delay=delay,
            duration_ticks=duration_ticks,
            delay_ticks=delay_ticks,
        )

    def right_click(
        self,
        duration: float = 0.05,
        delay: float = 0.0,
        *,
        duration_ticks: int = 0,
        delay_ticks: int = 0,
    ):
        """Shortcut for ``click(MouseButton.RIGHT, ...)``."""
        self.click(
            MouseButton.RIGHT,
            duration=duration,
            delay=delay,
            duration_ticks=duration_ticks,
            delay_ticks=delay_ticks,
        )

    def middle_click(
        self,
        duration: float = 0.05,
        delay: float = 0.0,
        *,
        duration_ticks: int = 0,
        delay_ticks: int = 0,
    ):
        """Shortcut for ``click(MouseButton.MIDDLE, ...)``."""
        self.click(
            MouseButton.MIDDLE,
            duration=duration,
            delay=delay,
            duration_ticks=duration_ticks,
            delay_ticks=delay_ticks,
        )
