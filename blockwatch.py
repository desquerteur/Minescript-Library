# SPDX-License-Identifier: MIT
"""Watch the targeted block for changes: \\blockwatch [SECONDS]."""

import sys

import minescript as m

from automation_common import Session, Stopped, duration, run


def main(args):
    seconds = duration(args)
    target = m.player_get_targeted_block(8)
    if target is None:
        raise Stopped("Look at a block within 8 blocks before starting.")
    pos = tuple(target.position)
    with Session(seconds) as session:
        previous = m.getblock(*pos)
        m.echo(f"Watching {pos}: {previous}")
        while True:
            session.wait(0.25)
            current = m.getblock(*pos)
            if current != previous:
                m.echo(f"{pos}: {previous} -> {current}")
                previous = current


if __name__ == "__main__":
    run(main, sys.argv[1:])
