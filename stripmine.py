# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Mine continuously: \\stripmine [LENGTH|forever] [SECONDS|forever]. F8 stops."""

import math
import sys
import time
from itertools import repeat

import minescript as m

from automation_common import (
    UNLIMITED,
    Session,
    Stopped,
    block_id,
    break_block,
    duration,
    held_item,
    run,
)

AIR = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}
NATURAL = {
    "minecraft:stone",
    "minecraft:deepslate",
    "minecraft:cobblestone",
    "minecraft:cobbled_deepslate",
    "minecraft:granite",
    "minecraft:diorite",
    "minecraft:andesite",
    "minecraft:tuff",
    "minecraft:calcite",
    "minecraft:netherrack",
    "minecraft:basalt",
    "minecraft:smooth_basalt",
    "minecraft:blackstone",
    "minecraft:dirt",
    "minecraft:coarse_dirt",
    "minecraft:rooted_dirt",
    "minecraft:grass_block",
    "minecraft:clay",
}
FALLING = {"minecraft:gravel", "minecraft:sand", "minecraft:red_sand"}
DANGER = {
    "minecraft:lava",
    "minecraft:water",
    "minecraft:bubble_column",
    "minecraft:fire",
    "minecraft:soul_fire",
    "minecraft:magma_block",
    "minecraft:powder_snow",
    "minecraft:cactus",
}


def integer(text, label, maximum=None):
    number = int(text)
    if number < 1 or maximum is not None and number > maximum:
        bound = f"between 1 and {maximum}" if maximum is not None else "positive"
        raise ValueError(f"{label} must be {bound}.")
    return number


def length_limit(text=None):
    if text is None or str(text).strip().casefold() in UNLIMITED:
        return None
    return integer(text, "Length")


def direction(yaw):
    """Nearest cardinal direction: Minecraft yaw 0 faces south."""
    return ((0, 1), (-1, 0), (0, -1), (1, 0))[round(yaw / 90) % 4]


def natural(state):
    name = block_id(state)
    return name in NATURAL or name.startswith("minecraft:") and name.endswith("_ore")


def survey(cell):
    """Check the next tunnel cell, its floor, ceiling, and immediate neighbors."""
    x, y, z = cell
    positions = {(x, y - 1, z), (x, y + 2, z)}
    for level in (y, y + 1):
        positions.update(
            {
                (x, level, z),
                (x - 1, level, z),
                (x + 1, level, z),
                (x, level, z - 1),
                (x, level, z + 1),
            }
        )
    positions = sorted(positions)
    states = dict(zip(positions, m.getblocklist([list(pos) for pos in positions]), strict=True))
    for pos, state in states.items():
        name = block_id(state)
        if name in DANGER or "waterlogged=true" in state:
            raise Stopped(f"Hazard beside the tunnel at {pos}: {state}")
    floor = states[(x, y - 1, z)]
    if not natural(floor) and block_id(floor) not in {"minecraft:bedrock", "minecraft:obsidian"}:
        raise Stopped("The next step does not have a supported solid floor.")
    ceiling = block_id(states[(x, y + 2, z)])
    if ceiling in FALLING or ceiling.endswith("_concrete_powder") or ceiling.endswith("anvil"):
        raise Stopped("Falling blocks above the tunnel; stopped before mining.")
    return states


class MiningSession(Session):
    def check(self):
        super().check()
        item, count = held_item()
        if not item.endswith("_pickaxe") or count < 1:
            raise Stopped("Hold a pickaxe; it may have broken or been switched.")
        slots = {
            item.slot
            for item in m.player_inventory()
            if item.slot is not None and 0 <= item.slot <= 35 and item.count > 0
        }
        if len(slots) == 36:
            raise Stopped("Inventory is full. Make space before continuing.")


def advance(session, cell):
    states = survey(cell)
    x, y, z = cell
    # Headroom first. Reject containers, builds, and unsupported materials.
    for pos in ((x, y + 1, z), (x, y, z)):
        session.check()
        state = states[pos]
        if block_id(state) in AIR:
            continue
        if not natural(state) and block_id(state) not in FALLING:
            raise Stopped(f"Unsupported block in the tunnel at {pos}: {state}")
        if not break_block(session, pos, state):
            raise Stopped("Could not safely reach or break the next tunnel block.")
        states = survey(cell)
    states = survey(cell)
    if any(block_id(states[pos]) not in AIR for pos in ((x, y, z), (x, y + 1, z))):
        raise Stopped("The next tunnel cell is obstructed.")
    goal = (x + 0.5, z + 0.5)
    m.player_look_at(goal[0], y + 1.62, goal[1])
    session.wait(0.1)
    started = time.monotonic()
    try:
        while True:
            session.check()
            px, py, pz = m.player_position()
            if abs(py - y) > 0.25:
                raise Stopped("Player height changed; stopped moving.")
            distance = math.dist((px, pz), goal)
            if distance <= 0.15:
                return
            if distance > 1.8 or time.monotonic() - started > 4:
                raise Stopped("Movement blocked or player left the planned tunnel.")
            survey(cell)
            if m.player_get_targeted_entity(2) is not None:
                raise Stopped("An entity is in the tunnel; stopped moving.")
            # Release between short pulses so slower API queries do not keep
            # walking the player while checking the next position.
            m.player_look_at(goal[0], y + 1.62, goal[1])
            try:
                m.player_press_forward(True)
                time.sleep(0.04)
            finally:
                m.player_press_forward(False)
    finally:
        m.player_press_forward(False)


def follow_steps(steps, seconds):
    with MiningSession(seconds) as session:
        cell = tuple(math.floor(v) for v in m.player_position())
        for dx, dz in steps:
            session.check()
            cell = (cell[0] + dx, cell[1], cell[2] + dz)
            advance(session, cell)
        m.echo("Mining route completed.")


def main(args):
    if len(args) > 2:
        raise ValueError("Usage: \\stripmine [LENGTH|forever] [SECONDS|forever]")
    length = length_limit(args[0] if args else None)
    seconds = duration(args[1:])
    heading = direction(m.player_orientation()[0])
    steps = repeat(heading) if length is None else repeat(heading, length)
    follow_steps(steps, seconds)


if __name__ == "__main__":
    run(main, sys.argv[1:])
