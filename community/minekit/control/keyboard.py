"""Keyboard helpers for Minescript key binds."""

from __future__ import annotations

import time

import minescript

from ..internal.enums import KeyBind


class KeyboardController:
    """Thin wrapper around Minecraft key binds."""

    def __init__(self, *, sleep_fn=time.sleep):
        """Create a keyboard controller.

        Args:
            sleep_fn: Delay function used between key down and up calls.
        """
        self._sleep = sleep_fn

    def down(self, key_bind: KeyBind):
        """Press a Minecraft key bind without releasing it."""
        minescript.press_key_bind(KeyBind(key_bind).value, True)

    def up(self, key_bind: KeyBind):
        """Release a Minecraft key bind."""
        minescript.press_key_bind(KeyBind(key_bind).value, False)

    def tap(self, key_bind: KeyBind, duration: float = 0.05):
        """Press and release a Minecraft key bind.

        Args:
            key_bind: Which key bind to trigger.
            duration: How long the bind stays pressed.
        """
        key_bind = KeyBind(key_bind)
        self.down(key_bind)
        self._sleep(duration)
        self.up(key_bind)

    def spam(
        self,
        key_bind: KeyBind,
        count: int,
        press_time: float = 0.05,
        interval: float = 0.03,
    ):
        """Repeat a key bind press multiple times."""
        if count < 0:
            raise ValueError("count must be >= 0")
        for index in range(count):
            self.tap(key_bind, duration=press_time)
            if index + 1 < count and interval > 0:
                self._sleep(interval)
