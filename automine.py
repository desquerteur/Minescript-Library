# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Mine nearby matching blocks: \\automine BLOCK_ID [SECONDS]. No walking."""

import re
import sys

import minescript as m

from automation_common import (
    Session,
    Stopped,
    block_id,
    break_block,
    duration,
    held_item,
    nearby_blocks,
    run,
)


def main(args):
    if not args or not re.fullmatch(r"(?:[a-z0-9_.-]+:)?[a-z0-9_/.-]+", args[0]):
        raise ValueError("Usage: \\automine cobblestone [SECONDS]")
    target_id = args[0] if ":" in args[0] else "minecraft:" + args[0]
    if target_id in {"minecraft:air", "minecraft:water", "minecraft:lava", "minecraft:bedrock"}:
        raise ValueError("Choose a solid, breakable block.")
    seconds = duration(args[1:])
    with Session(seconds) as session:
        m.echo("Mining", target_id, "within reach. Hold the appropriate tool.")
        while True:
            session.check()
            held, count = held_item()
            if count < 1 or not held.endswith(("_pickaxe", "_axe", "_shovel", "_hoe")):
                raise Stopped("Hold a pickaxe, axe, shovel, or hoe to mine.")
            candidates = nearby_blocks(lambda state: block_id(state) == target_id)
            for pos, state in candidates[:12]:
                session.check()
                # Do not mine the floor under the player's feet.
                px, py, pz = m.player_position()
                if abs(pos[0] + 0.5 - px) < 0.8 and abs(pos[2] + 0.5 - pz) < 0.8 and pos[1] < py:
                    continue
                if break_block(session, pos, state):
                    break
            session.wait(0.25)


if __name__ == "__main__":
    run(main, sys.argv[1:])
