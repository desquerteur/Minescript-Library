# SPDX-License-Identifier: MIT
"""Count block types in a selection: \\regioncount X1 Y1 Z1 X2 Y2 Z2."""

import sys
from collections import Counter

import minescript as m

from automation_common import block_id, run
from library_tools import volume


def main(args):
    if len(args) != 6:
        raise ValueError("Usage: \\regioncount X1 Y1 Z1 X2 Y2 Z2; at most 8192 blocks.")
    values = [int(value) for value in args]
    blocks = volume(values[:3], values[3:])
    counts = Counter(block_id(state) for _, state in blocks)
    for name, count in counts.most_common(30):
        m.echo(f"{name}: {count}")
    m.echo(f"{len(blocks)} blocks, {len(counts)} block types; displaying up to 30 types.")


if __name__ == "__main__":
    run(main, sys.argv[1:])
