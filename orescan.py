# SPDX-License-Identifier: MIT
"""Locate ore in nearby loaded blocks: \\orescan [RADIUS]."""

import math
import sys

import minescript as m

from automation_common import block_id, run
from library_tools import around, radius


def main(args):
    origin = m.player_position()
    ores = [
        (pos, block_id(state))
        for pos, state in around(radius(args))
        if block_id(state).endswith("_ore") or block_id(state) == "minecraft:ancient_debris"
    ]
    ores.sort(key=lambda item: math.dist(origin, item[0]))
    for pos, name in ores[:30]:
        m.echo(f"{name} at {pos}; {math.dist(origin, pos):.1f} blocks")
    m.echo(f"{len(ores)} ore blocks in loaded client data; displaying up to 30.")


if __name__ == "__main__":
    run(main, sys.argv[1:])
