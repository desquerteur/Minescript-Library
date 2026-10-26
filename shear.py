# SPDX-License-Identifier: MIT
# Adapted from LaosyAlex/Scripts-For-MCSMP/shearsheep.py.
# Copyright (c) 2026 Alex Phommarath. See licenses/Scripts-For-MCSMP-MIT.txt.
"""Shear nearby sheep without walking: \\shear [SECONDS]. Hold shears."""

import sys
import time

import minescript as m

from automation_common import Session, duration, require_item, run


def main(args):
    seconds = duration(args)
    cooldowns = {}
    with Session(seconds) as session:
        while True:
            session.check()
            require_item("minecraft:shears")
            sheep = m.entities(type=r".*[.:]sheep", max_distance=3, sort="nearest")
            for entity in sheep:
                if time.monotonic() < cooldowns.get(entity.uuid, 0):
                    continue
                pos = entity.position
                m.player_look_at(pos[0], pos[1] + 0.8, pos[2])
                session.wait(0.1)
                target = m.player_get_targeted_entity(3)
                if target is not None and target.uuid == entity.uuid:
                    require_item("minecraft:shears")
                    session.use()
                    cooldowns[entity.uuid] = time.monotonic() + 10
                    break
                cooldowns[entity.uuid] = time.monotonic() + 2
            # Sheared sheep and lambs simply ignore the shears interaction.
            session.wait(0.25)


if __name__ == "__main__":
    run(main, sys.argv[1:])
