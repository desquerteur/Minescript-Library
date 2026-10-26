# SPDX-License-Identifier: MIT
# Adapted from LaosyAlex/Scripts-For-MCSMP/logAllEntities.py.
# Copyright (c) 2026 Alex Phommarath. See licenses/Scripts-For-MCSMP-MIT.txt.
"""Locate nearby animals or dropped items: \\nearby [RADIUS] [NAME_OR_TYPE]."""

import math
import sys

import minescript as m

from automation_common import run


def main(args):
    if len(args) > 2:
        raise ValueError("Usage: \\nearby [RADIUS] [NAME_OR_TYPE]")
    radius = float(args[0]) if args else 16.0
    if not math.isfinite(radius) or not 1 <= radius <= 64:
        raise ValueError("Radius must be between 1 and 64 blocks.")
    query = args[1].casefold() if len(args) > 1 else ""
    origin = m.player_position()
    entities = [
        entity
        for entity in m.entities(max_distance=radius, sort="nearest")
        if not entity.local and (query in entity.name.casefold() or query in entity.type.casefold())
    ]
    for entity in entities[:20]:
        x, y, z = entity.position
        distance = math.dist(origin, entity.position)
        m.echo(f"{entity.name} ({entity.type}) | {distance:.1f} blocks | {x:.1f}, {y:.1f}, {z:.1f}")
    if not entities:
        m.echo("No matching loaded entities nearby.")
    elif len(entities) > 20:
        m.echo(
            f"Showing the nearest 20 of {len(entities)} matches. Use a smaller radius or filter."
        )


if __name__ == "__main__":
    run(main, sys.argv[1:])
