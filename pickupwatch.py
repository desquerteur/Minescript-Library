# SPDX-License-Identifier: MIT
"""Report item pickup events for your player: \\pickupwatch [SECONDS]."""

import queue
import sys

import minescript as m

from automation_common import Session, duration, run


def main(args):
    seconds = duration(args)
    own_uuid = m.player().uuid
    with m.EventQueue() as events, Session(seconds) as session:
        events.register_take_item_listener()
        while True:
            session.wait(0.1)
            while True:
                try:
                    event = events.get(block=False)
                except queue.Empty:
                    break
                if event.player_uuid == own_uuid:
                    m.echo(f"Picked up {event.amount}: {event.item.name}")


if __name__ == "__main__":
    run(main, sys.argv[1:])
