# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Dig a main tunnel and paired side branches: \\branchmine LENGTH SPACING BRANCH [SECONDS]."""

import sys

import minescript as m

from automation_common import duration, run
from stripmine import direction, follow_steps, integer


def route(heading, length, spacing, branch):
    dx, dz = heading
    left = (dz, -dx)
    right = (-dz, dx)
    result = []
    for step in range(1, length + 1):
        result.append(heading)
        if step % spacing == 0:
            result.extend([left] * branch + [right] * branch)
            result.extend([right] * branch + [left] * branch)
    return result


def main(args):
    if not 3 <= len(args) <= 4:
        raise ValueError("Usage: \\branchmine LENGTH SPACING BRANCH [SECONDS]")
    length = integer(args[0], "Main tunnel length", 64)
    spacing = integer(args[1], "Branch spacing", 16)
    branch = integer(args[2], "Branch length", 16)
    steps = route(direction(m.player_orientation()[0]), length, spacing, branch)
    follow_steps(steps, duration(args[3:]))


if __name__ == "__main__":
    run(main, sys.argv[1:])
