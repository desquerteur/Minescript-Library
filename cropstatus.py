# SPDX-License-Identifier: MIT
"""Count ripe and growing crops nearby: \\cropstatus [RADIUS]."""

import sys
from collections import Counter

import minescript as m

from automation_common import block_id, run
from farm import CROPS, mature
from library_tools import around, radius


def main(args):
    ripe, growing = Counter(), Counter()
    for _, state in around(radius(args)):
        name = block_id(state)
        if name in CROPS:
            (ripe if mature(state) else growing)[name] += 1
    for name in sorted(ripe.keys() | growing.keys()):
        m.echo(f"{name}: {ripe[name]} ripe, {growing[name]} growing")
    if not ripe and not growing:
        m.echo("No supported crops in the loaded scan volume.")


if __name__ == "__main__":
    run(main, sys.argv[1:])
