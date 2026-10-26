# SPDX-License-Identifier: MIT
"""Show chunk and within-chunk block coordinates: \\chunkcoords."""

import math
import sys

import minescript as m

from automation_common import run


def main(args):
    if args:
        raise ValueError("Usage: \\chunkcoords")
    x, y, z = (math.floor(value) for value in m.player_position())
    m.echo(f"Block: {x}, {y}, {z}")
    m.echo(f"Chunk: {x // 16}, {z // 16}; local block: {x % 16}, {z % 16}")


if __name__ == "__main__":
    run(main, sys.argv[1:])
