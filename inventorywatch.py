# SPDX-License-Identifier: MIT
"""Report increases and decreases in carried supplies: \\inventorywatch [SECONDS]."""

import sys

import minescript as m

from automation_common import Session, duration, run
from library_tools import supplies


def main(args):
    with Session(duration(args)) as session:
        previous = supplies()
        while True:
            session.wait(0.5)
            current = supplies()
            for name in sorted(current.keys() | previous.keys()):
                delta = current[name] - previous[name]
                if delta:
                    m.echo(f"{name}: {delta:+d}; now {current[name]}")
            previous = current


if __name__ == "__main__":
    run(main, sys.argv[1:])
