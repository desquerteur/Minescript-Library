# SPDX-License-Identifier: MIT
"""Calculate distance and yaw/pitch to coordinates: \\bearing X Y Z."""

import math
import sys

import minescript as m

from automation_common import run
from library_tools import point


def main(args):
    target = point(args)
    x, y, z = m.player_position()
    dx, dy, dz = target[0] - x, target[1] - y - 1.62, target[2] - z
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = -math.degrees(math.atan2(dy, math.hypot(dx, dz)))
    m.echo(f"Distance from feet: {math.dist((x, y, z), target):.2f} blocks")
    m.echo(f"Aim from eyes: yaw {yaw:.1f}, pitch {pitch:.1f}")


if __name__ == "__main__":
    run(main, sys.argv[1:])
