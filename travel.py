# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
r"""Walk with auto-eating: \travel X Z or \travel X Y Z [--eat-at 14] [--check].

F8/menu stops. Carry ordinary food. Routes over full blocks, one-block steps
and drops, plus surface swimming; does not dig, place blocks or use portals.
"""

import heapq
import math
import re
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


def water(state):
    if name(state) in {"kelp", "kelp_plant", "seagrass", "tall_seagrass"}:
        return True
    if name(state) != "water":
        return False
    level = re.search(r"(?:\[|,)level=(\d+)(?:,|\])", state)
    return level is None or int(level[1]) < 8  # Downward waterfalls are not surface routes.


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

    def swimmable(self, pos):
        x, y, z = pos
        return (
            self.clear(pos)
            and water(self.at((x, y - 1, z)))
            and all(
                name(self.at((x + dx, y, z + dz))) not in {"cactus", "fire", "soul_fire", "lava"}
                for dx, dz in ((0, 1), (1, 0), (0, -1), (-1, 0))
            )
        )

    def traversable(self, pos):
        return self.standable(pos) or self.swimmable(pos)

    def edge(self, start, end):
        if not self.traversable(end):
            return False
        # Head clearance while rising and while crossing into a lower block.
        x, y, z = start
        ex, ey, ez = end
        dx, dz = ex - x, ez - z
        if max(abs(dx), abs(dz)) != 1 or abs(ey - y) > 1:
            return False
        if dx and dz:
            # Diagonal motion needs both side cells clear, including their floors.
            return ey == y and self.traversable((ex, y, z)) and self.traversable((x, y, ez))
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
        for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            other = x + dx, y, z + dz
            if self.edge(pos, other):
                yield other

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


def navigation_cell(position, *, afloat=False):
    if not afloat:
        return cell(position)
    x, y, z = (math.floor(value) for value in position)
    positions = [(x, level, z) for level in range(y - 2, y + 19)]
    terrain = Terrain(
        dict(zip(positions, m.getblocklist([list(pos) for pos in positions]), strict=True))
    )
    for level in range(y - 1, y + 17):
        candidate = (x, level, z)
        if terrain.swimmable(candidate):
            return candidate
    # Leaving water may put the center over the bank before the water-contact
    # flag clears. Project onto its full-block floor instead of rejecting bobbing.
    for level in sorted(range(y - 1, y + 3), key=lambda value: abs(value - position[1])):
        candidate = (x, level, z)
        if abs(level - position[1]) <= 1.1 and terrain.standable(candidate):
            return candidate
    raise Stopped("No open water surface or reachable bank found nearby. Take control.")


def arrived(destination, position, *, afloat=False, submerged=False):
    if submerged:
        return False
    if destination.reached(position):
        return True
    if not afloat or destination.distance(position) > 0.85 or destination.y is None:
        return False
    x, y, z = math.floor(destination.x), round(destination.y), math.floor(destination.z)
    if not -1.1 <= position[1] - y <= 1.35:
        return False
    below, feet, head = m.getblocklist([[x, y - 1, z], [x, y, z], [x, y + 1, z]])
    return water(below) and passable(feet) and passable(head)


def plan(terrain, start, destination, recent=(), limit=8000):
    """A* inside loaded local terrain, with a frontier waypoint for long trips."""
    if not terrain.traversable(start):
        raise Stopped("Your starting floor, water surface or headroom is unsupported.")
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
            score = (
                cost[current]
                + math.hypot(other[0] - current[0], other[2] - current[2])
                + abs(other[1] - current[1]) * 0.5
                + penalty[other] * 4
            )
            if score < cost.get(other, math.inf):
                cost[other], previous[other] = score, current
                heapq.heappush(frontier, (score + remaining(other), next(sequence), other))
    if best == start:
        raise Stopped(
            "No walking/swimming route found locally. A cliff, wall or unknown terrain blocks it."
        )
    path = [best]
    while path[-1] != start:
        path.append(previous[path[-1]])
    return list(reversed(path[:-1]))


def recheck_edge(start, end):
    return recheck_edges(start, [end])


def recheck_edges(start, ends):
    terrain = route_terrain(start, ends)
    previous = start
    for end in ends:
        if not terrain.edge(previous, end):
            return False
        previous = end
    return True


def route_terrain(start, ends):
    positions = set()
    cells = {start, *ends}
    previous = start
    for end in ends:
        if end[0] != previous[0] and end[2] != previous[2]:
            cells.update({(end[0], end[1], previous[2]), (previous[0], end[1], end[2])})
        previous = end
    for x, y, z in cells:
        positions.update((x, y + dy, z) for dy in (-1, 0, 1, 2))
        positions.update((x + dx, y, z + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    positions = sorted(positions)
    terrain = Terrain(
        dict(zip(positions, m.getblocklist([list(pos) for pos in positions]), strict=True))
    )
    return terrain


def move(session, start, end):
    """Precision movement for an elevation change; flat routes use Walker."""
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


def heading(start, end):
    return end[0] - start[0], end[2] - start[2]


def straight_run(start, path):
    direction = heading(start, path[0])
    previous, last = start, start
    for end in path:
        if end[1] != start[1] or heading(previous, end) != direction:
            break
        previous = last = end
    return last


def steering_target(position, start, path):
    dx, dz = heading(start, path[0])
    lateral = abs(
        (position[0] - start[0] - 0.5) * dz - (position[2] - start[2] - 0.5) * dx
    ) / math.hypot(dx, dz)
    # A distant aim point only slowly centers an off-center start. Center on
    # the first waypoint before extending the lookahead, without releasing W.
    return path[0] if lateral > 0.15 else straight_run(start, path)


def passed(position, start, end, *, afloat=False):
    """Accept a crossed waypoint plane so a delayed sample cannot turn us back."""
    dx, dz = heading(start, end)
    length = math.hypot(dx, dz)
    ox, oz = position[0] - end[0] - 0.5, position[2] - end[2] - 0.5
    along = (ox * dx + oz * dz) / length
    across = abs(ox * dz - oz * dx) / length
    height_ok = (
        (-1.1 <= position[1] - end[1] <= 1.35) if afloat else abs(position[1] - end[1]) < 0.2
    )
    return height_ok and (math.hypot(ox, oz) < 0.2 or -0.12 <= along <= 1.5 and across < 0.28)


class Walker:
    """Hold forward across waypoints and buffered straight-route refreshes."""

    def __init__(self, session):
        self.session = session
        self.walking = False
        self.floating = False

    def float(self, enabled):
        if self.floating != enabled:
            m.player_press_jump(enabled)
            if enabled:
                release("sprint")
            self.floating = enabled

    def surface(self):
        if self.walking:
            release("forward")
            self.walking = False
        self.float(True)
        surface_y = navigation_cell(self.session.position, afloat=True)[1]
        started = time.monotonic()
        while self.session.client.underwater() or self.session.position[1] < surface_y - 0.9:
            self.session.check()
            if time.monotonic() - started > 12:
                raise Stopped("Could not reach breathable surface water. Take control.")
            time.sleep(0.05)
        self.session.check(force=True)

    def stop(self):
        if self.walking or self.floating:
            release("forward", "jump")
            self.walking = False
            self.floating = False

    def follow(self, start, path, destination=None, *, refresh=False):
        completed = []
        next_check = 0.0
        aim = None
        terrain = None
        last_position, last_progress = self.session.position, time.monotonic()
        while path:
            self.session.check()
            position = self.session.position
            in_water = self.session.client.in_water()
            if in_water and (self.session.client.underwater() or position[1] < start[1] - 0.9):
                self.surface()
                last_position, last_progress = self.session.position, time.monotonic()
                continue
            if destination is not None and arrived(destination, position, afloat=in_water):
                self.stop()
                return completed, False
            if math.hypot(position[0] - last_position[0], position[2] - last_position[2]) > 0.05:
                last_position, last_progress = position, time.monotonic()
            elif time.monotonic() - last_progress > 3:
                self.stop()
                return completed, True
            end = path[0]
            for offset, candidate in enumerate(path[1:], 1):
                if (math.floor(position[0]), math.floor(position[2])) == (
                    candidate[0],
                    candidate[2],
                ) and abs(position[1] - candidate[1]) < (1.4 if in_water else 0.3):
                    # A slow bridge call can let the player cross several known
                    # cells. Resume from that route cell rather than walking back
                    # or declaring that the player left the route.
                    completed.extend(path[:offset])
                    start, path = path[offset - 1], path[offset:]
                    terrain, aim = None, None
                    break
            end = path[0]
            if terrain is None or time.monotonic() >= next_check:
                terrain = route_terrain(start, path[:4])
                previous = start
                for target in path[:4]:
                    if not terrain.edge(previous, target):
                        self.stop()
                        return completed, True
                    previous = target
                next_check = time.monotonic() + 0.15
            wet = in_water or terrain.swimmable(start) or terrain.swimmable(end)
            self.float(wet)
            if end[1] != start[1] and not wet:
                self.stop()
                if not move(self.session, start, end):
                    return completed, True
                completed.append(end)
                start, path = end, path[1:]
                last_progress, aim = time.monotonic(), None
                continue
            if passed(position, start, end, afloat=wet) and (wet or self.session.client.grounded()):
                completed.append(end)
                start, path = end, path[1:]
                if (
                    refresh
                    and len(completed) >= 4
                    and len(path) >= 6
                    and straight_run(start, path[:6]) == path[5]
                ):
                    # Keep walking only with six validated, straight, flat cells
                    # remaining while the next local scan and route are computed.
                    if not recheck_edges(start, path[:6]):
                        self.stop()
                        return completed, True
                    return completed, False
                continue
            px, py, pz = position
            if wet and math.hypot(px - end[0] - 0.5, pz - end[2] - 0.5) > 2.5:
                self.stop()
                return completed, False  # A current may require a new route.
            height_ok = (
                min(start[1], end[1]) - 1.4 <= py <= max(start[1], end[1]) + 1.4
                if wet
                else abs(py - end[1]) <= 0.4
            )
            if math.hypot(px - end[0] - 0.5, pz - end[2] - 0.5) > 2.5 or not height_ok:
                raise Stopped("Player left the walking route. Take control.")
            if self.session.eat(stay_afloat=wet):
                # Eating releases movement itself. Reset our input state and
                # progress clock before resuming; do not count eating as stuck.
                self.walking, aim = False, None
                self.session.check(force=True)
                last_position, last_progress = self.session.position, time.monotonic()
                continue
            target = steering_target(position, start, path)
            if aim != target:
                m.player_look_at(target[0] + 0.5, py + 1.62, target[2] + 0.5)
                aim = target
            if not self.walking:
                m.player_press_forward(True)
                self.walking = True
            time.sleep(0.03)
        self.stop()
        return completed, False


def main(args):
    options = arguments(args)
    exclusive()
    client = Client()
    position = m.player_position()
    in_water = client.in_water()
    if not client.grounded() and not in_water:
        raise Stopped("Start on the ground or in open surface water.")
    destination = options.destination
    if arrived(destination, position, afloat=in_water, submerged=in_water and client.underwater()):
        m.echo("Already at the destination.")
        return
    if options.check:
        current = navigation_cell(position, afloat=in_water)
        projected = (current[0] + 0.5, current[1], current[2] + 0.5)
        path = (
            []
            if destination.reached(projected)
            else plan(Terrain.scan(current), current, destination)
        )
        m.echo(f"Walking check: hunger {client.food_level()}/20; local route {len(path)} steps.")
        m.echo("Read-only check complete. Run without --check to travel.")
        return
    with Session(client, options.eat_at) as session:
        recent = deque(maxlen=160)
        failures = 0
        best_distance, progress_time = destination.distance(session.position), time.monotonic()
        report_at = 0
        walker = Walker(session)
        try:
            if in_water:
                walker.surface()
            while not arrived(
                destination,
                session.position,
                afloat=client.in_water(),
                submerged=client.underwater(),
            ):
                session.check(force=True)
                current = navigation_cell(
                    session.position, afloat=client.in_water() or walker.floating
                )
                path = plan(Terrain.scan(current), current, destination, recent)
                session.check(force=True)
                if arrived(
                    destination,
                    session.position,
                    afloat=client.in_water(),
                    submerged=client.underwater(),
                ):
                    break
                actual = navigation_cell(
                    session.position, afloat=client.in_water() or walker.floating
                )
                if actual != current:
                    # Planning can finish after we have already crossed cells.
                    # Trim those cells instead of steering back toward them.
                    if actual not in path:
                        walker.stop()
                        continue
                    path = path[path.index(actual) + 1 :]
                    current = actual
                    if not path:
                        walker.stop()
                        continue
                completed, blocked = walker.follow(current, path, destination, refresh=True)
                recent.extend([current, *completed[:-1]])
                if blocked:
                    failures += 1
                    if failures >= 3:
                        raise Stopped(
                            "Walking is blocked after three route attempts. Take control."
                        )
                else:
                    failures = 0
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
        finally:
            walker.stop()
        m.echo("Arrived at the walking destination.")


if __name__ == "__main__":
    run(main)
