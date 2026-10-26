"""Controller facade for time and tick-based waits."""

from __future__ import annotations

from ..game.timing import (
    SECONDS_PER_TICK,
    TICKS_PER_SECOND,
    current_game_tick,
    seconds_to_ticks,
    ticks_to_seconds,
    wait_ticks,
)


class TimingController:
    """Facade for waiting in seconds or Minecraft ticks."""

    def current_tick(self) -> int:
        """Return the current absolute Minecraft game tick."""
        return current_game_tick()

    def to_ticks(self, seconds: float) -> int:
        """Convert seconds to Minecraft ticks using the standard 20 TPS baseline."""
        return seconds_to_ticks(seconds)

    def to_seconds(self, ticks: int) -> float:
        """Convert Minecraft ticks to seconds using the standard 20 TPS baseline."""
        return ticks_to_seconds(ticks)

    def wait_ticks(self, ticks: int) -> int:
        """Wait for a number of Minecraft ticks to elapse."""
        return wait_ticks(ticks)

    def wait_seconds(self, seconds: float) -> int:
        """Wait for roughly ``seconds`` using Minecraft ticks as the clock source."""
        return wait_ticks(seconds_to_ticks(seconds))

    def sleep(self, seconds: float | None = None, *, ticks: int | None = None) -> int:
        """Wait using either seconds or ticks.

        Args:
            seconds: Friendly time value converted to ticks under the hood.
            ticks: Explicit number of Minecraft ticks to wait.

        Returns:
            The game tick observed when the wait completes.
        """
        if ticks is not None:
            return self.wait_ticks(ticks)
        if seconds is not None:
            return self.wait_seconds(seconds)
        raise ValueError("sleep() expects either seconds=... or ticks=...")


__all__ = [
    "SECONDS_PER_TICK",
    "TICKS_PER_SECOND",
    "TimingController",
]
