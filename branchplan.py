# SPDX-License-Identifier: MIT
"""Preview branch-tunnel coordinates without mining: \\branchplan LENGTH SPACING BRANCH."""

import math
import sys

import minescript as m

from automation_common import run
from stripmine import direction, integer


def main(args):
    if len(args) != 3:
        raise ValueError("Usage: \\branchplan LENGTH SPACING BRANCH")
    length, spacing, branch = (
        integer(value, label, bound)
        for value, label, bound in zip(
            args, ("Length", "Spacing", "Branch"), (64, 16, 16), strict=True
        )
    )
    x, y, z = (math.floor(value) for value in m.player_position())
    dx, dz = direction(m.player_orientation()[0])
    m.echo(f"Main tunnel: {(x, y, z)} to {(x + dx * length, y, z + dz * length)}")
    for step in range(spacing, length + 1, spacing):
        cx, cz = x + dx * step, z + dz * step
        m.echo(
            f"Branch at {(cx, y, cz)}: {(cx + dz * branch, y, cz - dx * branch)}"
            f" to {(cx - dz * branch, y, cz + dx * branch)}"
        )
    m.echo("Coordinate preview complete; no blocks changed.")


if __name__ == "__main__":
    run(main, sys.argv[1:])
