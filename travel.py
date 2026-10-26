# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
r"""Walk with auto-eating: \travel X Z or \travel X Y Z [--eat-at 14] [--check].

F8/menu stops. Carry ordinary food. Routes over full blocks, one-block steps
and drops; does not dig, place blocks, swim, or use portals. No time limit.
"""

import heapq
import math
import time
from collections import Counter, deque
from itertools import count

import minescript as m

from travel_common import Client, Session, Stopped, arguments, exclusive, release, run

AIR = {"air", "cave_air", "void_air", "short_grass", "tall_grass", "fern", "large_fern"}
PLANTS = {
    "dandelion",
    "poppy",
    "blue_orchid",
    "allium",
    "azure_bluet",
    "oxeye_daisy",
    "cornflower",
    "lily_of_the_valley",
    "torchflower",
    "pink_petals",
    "wildflowers",
    "sunflower",
    "lilac",
    "rose_bush",
    "peony",
    "wheat",
    "carrots",
    "potatoes",
    "beetroots",
    "dead_bush",
    "brown_mushroom",
    "red_mushroom",
}
FLOORS = {
    "stone",
    "deepslate",
    "dirt",
    "coarse_dirt",
    "rooted_dirt",
    "dirt_path",
    "farmland",
    "sand",
    "red_sand",
    "gravel",
    "clay",
    "granite",
    "diorite",
    "andesite",
    "tuff",
    "calcite",
    "netherrack",
    "basalt",
    "smooth_basalt",
    "blackstone",
    "obsidian",
    "crying_obsidian",
    "bedrock",
    "cobblestone",
    "mossy_cobblestone",
    "bricks",
    "stone_bricks",
    "mossy_stone_bricks",
    "cracked_stone_bricks",
    "chiseled_stone_bricks",
    "sandstone",
    "red_sandstone",
    "smooth_sandstone",
    "smooth_red_sandstone",
    "end_stone",
    "end_stone_bricks",
    "terracotta",
    "glass",
    "packed_ice",
    "blue_ice",
}
BAD = {"magma_block", "honey_block", "slime_block", "powder_snow"}


def name(state):
    return state.split("[", 1)[0].removeprefix("minecraft:")


def passable(state):
    block = name(state)
    return "waterlogged=true" not in state and (
        block in AIR | PLANTS
        or block.endswith("_sapling")
        or block == "snow"
        and "layers=1" in state
    )


def support(state):
    block = name(state)
    return (
        "waterlogged=true" not in state
        and block not in BAD
        and (
            block in FLOORS
            or block
            in {"crimson_stem", "warped_stem", "stripped_crimson_stem", "stripped_warped_stem"}
            or block.endswith(
                (
                    "_planks",
                    "_log",
                    "_wood",
                    "_hyphae",
                    "_ore",
                    "_wool",
                    "_concrete",
                    "_terracotta",
                    "_stained_glass",
                    "_block",
                )
            )
            or block.endswith("_slab")
            and "type=double" in state
        )
    )


def cell(position):
    y = round(position[1])
    if abs(position[1] - y) > 0.2:
        raise Stopped("Start on level full blocks, not a slab, stair, ladder or in water.")
    return math.floor(position[0]), y, math.floor(position[2])


class Terrain:
    def __init__(self, states):
        self.states = states

    def at(self, pos):
        return self.states.get(pos, "unknown")

    def clear(self, pos):
        x, y, z = pos
        return passable(self.at(pos)) and passable(self.at((x, y + 1, z)))

    def standable(self, pos):
        x, y, z = pos
        return (
            self.clear(pos)
            and support(self.at((x, y - 1, z)))
            and all(
                name(self.at((x + dx, y, z + dz))) not in {"cactus", "fire", "soul_fire", "lava"}
                for dx, dz in ((0, 1), (1, 0), (0, -1), (-1, 0))
            )
        )

    def edge(self, start, end):
        if not self.standable(end):
            return False
        # Head clearance while rising and while crossing into a lower block.
        x, y, z = start
        ex, ey, ez = end
        if ey > y and not passable(self.at((x, y + 2, z))):
            return False
        return ey >= y or passable(self.at((ex, y + 1, ez)))

    def neighbors(self, pos):
        x, y, z = pos
        for dx, dz in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            for dy in (0, 1, -1):
                other = x + dx, y + dy, z + dz
                if self.edge(pos, other):
                    yield other
                    break

    @classmethod
    def scan(cls, center, radius=12):
        x, y, z = center
        positions = [
            (bx, by, bz)
            for bx in range(x - radius, x + radius + 1)
            for bz in range(z - radius, z + radius + 1)
            for by in range(y - 5, y + 7)
        ]
        states = m.getblocklist([list(pos) for pos in positions])
        return cls(dict(zip(positions, states, strict=True)))


def plan(terrain, start, destination, recent=(), limit=8000):
    """A* inside loaded local terrain, with a frontier waypoint for long trips."""
    if not terrain.standable(start):
        raise Stopped(
            "Your starting floor or headroom is unsupported. Stand on a clear full block."
        )
    gx, gz = math.floor(destination.x), math.floor(destination.z)
    target_y = None if destination.y is None else round(destination.y)

    def remaining(pos):
        return math.hypot(pos[0] - gx, pos[2] - gz) + (
            0 if target_y is None else abs(pos[1] - target_y) * 1.5
        )

    penalty = Counter(recent)
    sequence = count()
    frontier = [(remaining(start), next(sequence), start)]
    cost, previous = {start: 0.0}, {}
    best = start
    examined = set()
    while frontier and len(examined) < limit:
        _, _, current = heapq.heappop(frontier)
        if current in examined:
            continue
        examined.add(current)
        if (current[0], current[2]) == (gx, gz) and (target_y is None or current[1] == target_y):
            best = current
            break
        if remaining(current) + penalty[current] * 4 < remaining(best) + penalty[best] * 4:
            best = current
        for other in terrain.neighbors(current):
            score = cost[current] + 1 + abs(other[1] - current[1]) * 0.5 + penalty[other] * 4
            if score < cost.get(other, math.inf):
                cost[other], previous[other] = score, current
                heapq.heappush(frontier, (score + remaining(other), next(sequence), other))
    if best == start:
        raise Stopped(
            "No walking route found locally. Water, a cliff, wall or unknown terrain blocks it."
        )
    path = [best]
    while path[-1] != start:
        path.append(previous[path[-1]])
    return list(reversed(path[:-1]))


def recheck_edge(start, end):
    positions = set()
    for x, y, z in (start, end):
        positions.update((x, y + dy, z) for dy in (-1, 0, 1, 2))
        positions.update((x + dx, y, z + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    positions = sorted(positions)
    terrain = Terrain(
        dict(zip(positions, m.getblocklist([list(pos) for pos in positions]), strict=True))
    )
    return terrain.edge(start, end)


def move(session, start, end):
    """Short walking pulses, with controls released before bridge queries."""
    x, y, z = end
    goal = x + 0.5, z + 0.5
    began = time.monotonic()
    try:
        while time.monotonic() - began < 7:
            session.check(force=True)
            px, py, pz = session.position
            distance = math.hypot(goal[0] - px, goal[1] - pz)
            if distance < 0.18 and abs(py - y) < 0.2 and session.client.grounded():
                return True
            if distance > 2.4 or py < min(start[1], y) - 0.4:
                raise Stopped("Player left the walking route. Take control.")
            if not recheck_edge(start, end):
                return False
            session.eat()
            m.player_look_at(goal[0], py + 1.62, goal[1])
            try:
                # Upward steps need space and a real jump, not auto-jump settings.
                m.player_press_jump(y > start[1] and py < y)
                m.player_press_forward(True)
                time.sleep(min(0.10, max(0.02, distance / 7)))
            finally:
                release("forward", "jump")
        return False
    finally:
        release("forward", "jump")


def main(args):
    options = arguments(args)
    exclusive()
    client = Client()
    position = m.player_position()
    if not client.grounded():
        raise Stopped("Start walking while standing on the ground.")
    destination = options.destination
    if destination.reached(position):
        m.echo("Already at the destination.")
        return
    path = plan(Terrain.scan(cell(position)), cell(position), destination)
    if options.check:
        m.echo(f"Walking check: hunger {client.food_level()}/20; local route {len(path)} steps.")
        m.echo("Read-only check complete. Run without --check to travel.")
        return
    with Session(client, options.eat_at) as session:
        recent = deque(maxlen=160)
        failures = 0
        best_distance, progress_time = destination.distance(session.position), time.monotonic()
        report_at = 0
        while not destination.reached(session.position):
            session.check(force=True)
            session.eat()
            current = cell(session.position)
            path = plan(Terrain.scan(current), current, destination, recent)
            for step in path[:4]:
                if not move(session, current, step):
                    failures += 1
                    if failures >= 3:
                        raise Stopped(
                            "Walking is blocked after three route attempts. Take control."
                        )
                    break
                failures = 0
                recent.append(current)
                current = step
                session.check(force=True)
                if destination.reached(session.position):
                    break
            distance = destination.distance(session.position)
            if distance < best_distance - 1:
                best_distance, progress_time = distance, time.monotonic()
            if time.monotonic() - progress_time > 90:
                raise Stopped(
                    "No sustained route progress for 90 seconds. A larger obstacle needs help."
                )
            if time.monotonic() >= report_at:
                m.echo(f"Walking: {distance:.0f} blocks to destination.")
                report_at = time.monotonic() + 15
        m.echo("Arrived at the walking destination.")


if __name__ == "__main__":
    run(main)
