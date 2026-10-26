# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Mine branches continuously: \\branchmine [LENGTH|forever] [SPACING] [BRANCH] [SECONDS]."""

import sys
from itertools import count, repeat

import minescript as m

from automation_common import duration, run
from stripmine import direction, follow_steps, integer, length_limit


def route(heading, length, spacing, branch):
    dx, dz = heading
    left = (dz, -dx)
    right = (-dz, dx)
    for step in count(1) if length is None else range(1, length + 1):
        yield heading
        if step % spacing == 0:
            yield from repeat(left, branch)
            yield from repeat(right, branch)
            yield from repeat(right, branch)
            yield from repeat(left, branch)


def main(args):
    if len(args) > 4:
        raise ValueError("Usage: \\branchmine [LENGTH|forever] [SPACING] [BRANCH] [SECONDS]")
    length = length_limit(args[0] if args else None)
    spacing = integer(args[1], "Branch spacing") if len(args) > 1 else 4
    branch = integer(args[2], "Branch length") if len(args) > 2 else 6
    steps = route(direction(m.player_orientation()[0]), length, spacing, branch)
    follow_steps(steps, duration(args[3:]))


if __name__ == "__main__":
    run(main, sys.argv[1:])
