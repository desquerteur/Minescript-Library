# SPDX-License-Identifier: MIT
"""Show in-game clock and weather: \\worldclock."""

import sys

import minescript as m

from automation_common import run


def main(args):
    if args:
        raise ValueError("Usage: \\worldclock")
    world = m.world_info()
    ticks = world.day_ticks % 24000
    hour = (ticks // 1000 + 6) % 24
    minute = ticks % 1000 * 60 // 1000
    weather = "thunderstorm" if world.thundering else "raining" if world.raining else "clear"
    m.echo(f"Minecraft time: {hour:02d}:{minute:02d}; day-cycle ticks {ticks}")
    m.echo(f"Dimension: {world.dimension}; weather: {weather}")


if __name__ == "__main__":
    run(main, sys.argv[1:])
