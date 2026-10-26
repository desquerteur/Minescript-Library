# SPDX-License-Identifier: MIT
# Adapted from Thehatmans/MsAutoFishing, Copyright (c) 2026 Thehatmans.
# See licenses/MsAutoFishing-MIT.txt and SOURCES.md.
"""Auto-fish continuously: \\autofish [SECONDS|forever]. Hold a fishing rod."""

import math
import sys
import time

import minescript as m

from automation_common import Session, Stopped, duration, require_item, run


def bobbers():
    return {
        entity.uuid: entity
        for entity in m.entities(max_distance=32)
        if "fishing_bobber" in entity.type
    }


def cast(session):
    require_item("minecraft:fishing_rod")
    previous = set(bobbers())
    session.use()
    end = time.monotonic() + 3
    while time.monotonic() < end:
        session.wait(0.05)
        new = [entity for uid, entity in bobbers().items() if uid not in previous]
        if len(new) > 1:
            raise Stopped("Several new bobbers appeared; fish away from other players.")
        # Bind near the player after our cast, excluding existing bobbers.
        # Ownership is not exposed by the API.
        if new and math.dist(m.player_position(), new[0].position) <= 4.5:
            return new[0].uuid
    m.echo("No new bobber found; retrying the cast.")
    return None


def main(args):
    seconds = duration(args)
    with Session(seconds) as session:
        require_item("minecraft:fishing_rod")
        m.echo("Start with your rod reeled in; keep away from other fishing players.")
        while True:
            uid = cast(session)
            if uid is None:
                session.wait(1)
                continue
            born = time.monotonic()
            settled = False
            while True:
                session.wait(0.05)
                require_item("minecraft:fishing_rod")
                entity = bobbers().get(uid)
                if entity is None:
                    m.echo("The tracked bobber disappeared; casting again.")
                    session.wait(1)
                    break
                vx, vy, vz = entity.velocity
                age = time.monotonic() - born
                if age > 2 and abs(vy) < 0.02:
                    settled = True
                if settled and vy < -0.1 and abs(vx) < 0.3 and abs(vz) < 0.3:
                    session.use()
                    session.wait(0.7)
                    break
                if age > 90:
                    m.echo("No bite for 90 seconds; reeling in and casting again.")
                    session.use()
                    session.wait(0.7)
                    break


if __name__ == "__main__":
    run(main, sys.argv[1:])
