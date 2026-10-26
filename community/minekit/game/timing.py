"""Helpers for timing based on Minecraft game ticks."""

from __future__ import annotations

import time

import minescript

TICKS_PER_SECOND = 20
SECONDS_PER_TICK = 1 / TICKS_PER_SECOND


def current_game_tick() -> int:
    """Return the current absolute game tick from ``minescript.world_info()``."""
    return int(minescript.world_info().game_ticks)


def seconds_to_ticks(seconds: float) -> int:
    """Convert seconds to Minecraft ticks using the standard 20 TPS baseline."""
    return max(0, round(float(seconds) * TICKS_PER_SECOND))


def ticks_to_seconds(ticks: int) -> float:
    """Convert Minecraft ticks to seconds using the standard 20 TPS baseline."""
    return float(ticks) * SECONDS_PER_TICK


def wait_ticks(ticks: int, *, poll_interval: float = 0.01) -> int:
    """Wait until a number of Minecraft game ticks has elapsed.

    Args:
        ticks: Number of game ticks to wait. ``0`` returns immediately.
        poll_interval: Fallback host sleep used while polling the game tick counter.

    Returns:
        The game tick observed when the wait completes.
    """
    ticks = int(ticks)
    if ticks <= 0:
        return current_game_tick()

    start = current_game_tick()
    target = start + ticks

    while True:
        now = current_game_tick()
        if now >= target:
            return now
        time.sleep(poll_interval)
