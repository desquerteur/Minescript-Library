"""Small helpers for keyboard event polling and toggles."""

from __future__ import annotations

import queue

import minescript

from ..internal.enums import KeyCode

_KEY_UP = 0
_KEY_DOWN = 1
_KEY_REPEAT = 2


class HotkeyController:
    """Small event helper for keyboard-driven script toggles and polling."""

    def __init__(self):
        """Create an unbound hotkey controller.

        Use it as a context manager so the underlying Minescript listeners are
        registered and unregistered automatically.
        """
        self._queue = None

    def __enter__(self):
        """Open an event queue and start listening for key events."""
        self._queue = minescript.EventQueue()
        self._queue.__enter__()
        self._queue.register_key_listener()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the listener and release the underlying Minescript queue."""
        if self._queue is None:
            return False
        result = self._queue.__exit__(exc_type, exc_val, exc_tb)
        self._queue = None
        return result

    def poll(self, timeout: float = 0.0):
        """Return the next queued event or ``None`` when the timeout expires.

        Args:
            timeout: Seconds to wait for an event before returning ``None``.
        """
        if self._queue is None:
            raise RuntimeError("HotkeyController must be used inside a with block.")

        try:
            return self._queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def is_press(self, event, key_code: int | KeyCode, *, in_game_only: bool = True) -> bool:
        """Check whether an event is a key-down for the given key code."""
        return self._matches(event, key_code, _KEY_DOWN, in_game_only=in_game_only)

    def is_release(self, event, key_code: int | KeyCode, *, in_game_only: bool = True) -> bool:
        """Check whether an event is a key-up for the given key code."""
        return self._matches(event, key_code, _KEY_UP, in_game_only=in_game_only)

    def is_repeat(self, event, key_code: int | KeyCode, *, in_game_only: bool = True) -> bool:
        """Check whether an event is a key-repeat for the given key code."""
        return self._matches(event, key_code, _KEY_REPEAT, in_game_only=in_game_only)

    def wait_for_press(
        self,
        key_code: int | KeyCode,
        *,
        timeout: float | None = None,
        in_game_only: bool = True,
    ):
        """Block until the given key is pressed or the timeout expires.

        Args:
            key_code: GLFW key code or ``KeyCode`` constant to wait for.
            timeout: Max seconds to wait for a matching press. ``None`` waits forever.
            in_game_only: Ignore events fired while a GUI screen is open.
        """
        if self._queue is None:
            raise RuntimeError("HotkeyController must be used inside a with block.")

        while True:
            try:
                event = self._queue.get(block=True, timeout=timeout)
            except queue.Empty:
                return None

            if self.is_press(event, key_code, in_game_only=in_game_only):
                return event

    def toggle_on_press(
        self,
        key_code: int | KeyCode,
        state: bool,
        *,
        timeout: float = 0.0,
        in_game_only: bool = True,
    ) -> bool:
        """Flip a boolean state when the given key is pressed.

        Args:
            key_code: GLFW key code or ``KeyCode`` constant used as the toggle hotkey.
            state: Current boolean state.
            timeout: Seconds to wait for an event before returning the current state.
            in_game_only: Ignore events fired while a GUI screen is open.
        """
        event = self.poll(timeout=timeout)
        if self.is_press(event, key_code, in_game_only=in_game_only):
            return not state
        return state

    def _matches(
        self,
        event,
        key_code: int | KeyCode,
        action: int,
        *,
        in_game_only: bool,
    ) -> bool:
        if event is None:
            return False
        if getattr(event, "type", None) != minescript.EventType.KEY:
            return False
        if int(getattr(event, "key", -1)) != int(KeyCode(key_code)):
            return False
        if int(getattr(event, "action", -1)) != action:
            return False
        if in_game_only and getattr(event, "screen", None) is not None:
            return False
        return True
