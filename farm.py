# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Harvest and replant ripe nearby crops: \\farm [SECONDS]. Seeds in hotbar."""

import re
import sys

import minescript as m

from automation_common import (
    Session,
    Stopped,
    aim_block,
    block_id,
    break_block,
    duration,
    nearby_blocks,
    run,
)

CROPS = {
    "minecraft:wheat": (7, "minecraft:wheat_seeds"),
    "minecraft:carrots": (7, "minecraft:carrot"),
    "minecraft:potatoes": (7, "minecraft:potato"),
    "minecraft:beetroots": (3, "minecraft:beetroot_seeds"),
}


def mature(state):
    crop = CROPS.get(block_id(state))
    age = re.search(r"(?:\[|,)age=(\d+)(?:,|\])", state)
    return crop is not None and age is not None and int(age[1]) == crop[0]


def seed_slot(seed):
    return next(
        (
            item.slot
            for item in m.player_inventory()
            if item.item == seed
            and item.count > 0
            and item.slot is not None
            and 0 <= item.slot <= 8
        ),
        None,
    )


def main(args):
    seconds = duration(args)
    with Session(seconds) as session:
        while True:
            session.check()
            for pos, state in nearby_blocks(mature)[:12]:
                seed = CROPS[block_id(state)][1]
                slot = seed_slot(seed)
                if slot is None:
                    continue  # Never harvest a crop we cannot replant.
                m.player_inventory_select_slot(slot)
                session.wait(0.1)
                if not break_block(session, pos, state, timeout=2):
                    continue
                session.wait(0.2)
                below = (pos[0], pos[1] - 1, pos[2])
                if block_id(m.getblock(*below)) != "minecraft:farmland":
                    raise Stopped("Farmland changed; stopping before planting.")
                # Aim at the top of the farmland, rather than its buried center.
                if not aim_block(session, below, offset=0.99):
                    raise Stopped("Cannot see the farmland to replant; stopping.")
                if seed_slot(seed) is None:
                    raise Stopped("Seeds ran out; replant the last harvested crop manually.")
                session.use()
                session.wait(0.3)
                if block_id(m.getblock(*pos)) != block_id(state):
                    raise Stopped("Replanting failed; check the last harvested crop.")
                break
            session.wait(0.3)


if __name__ == "__main__":
    run(main, sys.argv[1:])
