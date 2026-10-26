# SPDX-License-Identifier: MIT
# Adapted from LaosyAlex/Scripts-For-MCSMP/getEntityInfo.py.
# Copyright (c) 2026 Alex Phommarath. See licenses/Scripts-For-MCSMP-MIT.txt.
"""Inspect the entity in your crosshair: \\entityinfo [RANGE]."""

import math
import sys

import minescript as m

from automation_common import run


def main(args):
    if len(args) > 1:
        raise ValueError("Usage: \\entityinfo [RANGE]")
    reach = float(args[0]) if args else 6.0
    if not math.isfinite(reach) or not 1 <= reach <= 64:
        raise ValueError("Range must be between 1 and 64 blocks.")
    entity = m.player_get_targeted_entity(reach)
    if entity is None:
        m.echo("Look directly at an entity within range, then run \\entityinfo again.")
        return
    x, y, z = entity.position
    m.echo(f"Name: {entity.name}")
    m.echo(f"Type: {entity.type}")
    m.echo(f"Position: {x:.2f}, {y:.2f}, {z:.2f}")
    if entity.health is not None:
        m.echo(f"Health: {entity.health:g}")
    m.echo(f"UUID: {entity.uuid}")


if __name__ == "__main__":
    run(main, sys.argv[1:])
