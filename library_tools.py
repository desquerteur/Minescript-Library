# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Bounded read-only queries shared by the library utilities."""

import math
from collections import Counter

import minescript as m


def point(args):
    if len(args) != 3:
        raise ValueError("Provide X Y Z coordinates.")
    result = tuple(float(value) for value in args)
    if not all(math.isfinite(value) for value in result):
        raise ValueError("Coordinates must be finite numbers.")
    return result


def radius(args, default=4, maximum=8):
    if len(args) > 1:
        raise ValueError("Provide at most one radius.")
    value = int(args[0]) if args else default
    if not 1 <= value <= maximum:
        raise ValueError(f"Radius must be between 1 and {maximum}.")
    return value


def volume(first, second, limit=8192):
    low = tuple(min(a, b) for a, b in zip(first, second, strict=True))
    high = tuple(max(a, b) for a, b in zip(first, second, strict=True))
    count = math.prod(b - a + 1 for a, b in zip(low, high, strict=True))
    if count > limit:
        raise ValueError(f"Selection is too large: {count} blocks; limit {limit}.")
    positions = [
        (x, y, z)
        for x in range(low[0], high[0] + 1)
        for y in range(low[1], high[1] + 1)
        for z in range(low[2], high[2] + 1)
    ]
    return list(zip(positions, m.getblocklist([list(pos) for pos in positions]), strict=True))


def around(distance):
    center = tuple(math.floor(value) for value in m.player_position())
    return volume(
        tuple(value - distance for value in center), tuple(value + distance for value in center)
    )


def supplies():
    counts = Counter()
    for item in m.player_inventory():
        if item.slot is not None and 0 <= item.slot <= 35 and item.count > 0:
            counts[item.item] += item.count
    return counts
