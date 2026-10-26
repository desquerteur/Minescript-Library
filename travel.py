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
from typing import Any

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

    def corridor(self, position, target, level):
        return all(self.traversable((x, level, z)) for x, z in swept_cells(position, target))

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
    # A distant goal must be projected onto the local scan along its bearing.
    # Choosing the nearest scan corner drove diagonal-first, then sideways.
    xs, zs = [p[0] for p in terrain.states], [p[2] for p in terrain.states]
    low_x, high_x, low_z, high_z = min(xs) + 1, max(xs) - 1, min(zs) + 1, max(zs) - 1
    dx, dz = destination.x - start[0] - 0.5, destination.z - start[2] - 0.5
    fraction = 1.0
    for origin, delta, low, high in (
        (start[0] + 0.5, dx, low_x + 0.5, high_x + 0.5),
        (start[2] + 0.5, dz, low_z + 0.5, high_z + 0.5),
    ):
        if delta > 0:
            fraction = min(fraction, max(0, (high - origin) / delta))
        elif delta < 0:
            fraction = min(fraction, max(0, (low - origin) / delta))
    if min(xs) <= gx <= max(xs) and min(zs) <= gz <= max(zs):
        fraction = 1.0
    if fraction < 1:
        gx, gz = (
            math.floor(start[0] + 0.5 + dx * fraction),
            math.floor(start[2] + 0.5 + dz * fraction),
        )
        target_y = None

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
    if (
        best == start
        and (start[0], start[2]) == (gx, gz)
        and (target_y is None or start[1] == target_y)
    ):
        return [start]
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


def swept_cells(position, target, radius=0.32):
    """Voxel cells touched by a player's full width along a straight segment."""
    dx, dz = target[0] - position[0], target[2] - position[2]
    result = set()
    for bx in range(
        math.floor(min(position[0], target[0]) - radius),
        math.floor(max(position[0], target[0]) + radius) + 1,
    ):
        for bz in range(
            math.floor(min(position[2], target[2]) - radius),
            math.floor(max(position[2], target[2]) + radius) + 1,
        ):
            low, high = 0.0, 1.0
            for origin, delta, bound in ((position[0], dx, bx), (position[2], dz, bz)):
                lower, upper = bound - radius - 1e-8, bound + 1 + radius + 1e-8
                if abs(delta) < 1e-12:
                    if not lower <= origin <= upper:
                        high = -1
                        break
                else:
                    first, last = (lower - origin) / delta, (upper - origin) / delta
                    low, high = max(low, min(first, last)), min(high, max(first, last))
            if low <= high:
                result.add((bx, bz))
    return result


def corridor_terrain(position, target, level, other_level=None):
    cells = swept_cells(position, target)
    levels = (level,) if other_level is None else (level, other_level)
    positions = {(x, y + dy, z) for x, z in cells for y in levels for dy in (-1, 0, 1, 2)}
    positions.update(
        (x + dx, y, z + dz)
        for x, z in cells
        for y in levels
        for dx, dz in ((0, 1), (1, 0), (0, -1), (-1, 0))
    )
    positions = sorted(positions)
    return Terrain(dict(zip(positions, m.getblocklist([list(p) for p in positions]), strict=True)))


def shortcut(position, start, path, terrain, distance=18):
    """Keep a committed forward span instead of chasing every grid-cell center."""
    best = None
    for index, point in enumerate(path):
        if point[1] != start[1]:
            break
        if index and terrain.swimmable(point) != terrain.swimmable(start):
            break
        target = point[0] + 0.5, point[1], point[2] + 0.5
        if math.hypot(target[0] - position[0], target[2] - position[2]) > distance:
            continue
        if terrain.corridor(position, target, point[1]):
            best = index
    return best


def safe_runway(terrain, position, target, level):
    dx, dz = target[0] - position[0], target[2] - position[2]
    length = math.hypot(dx, dz)
    steps = max(1, math.ceil(length / 0.2))
    distance = 0.0
    for step in range(steps + 1):
        point = (position[0] + dx * step / steps, level, position[2] + dz * step / steps)
        if not terrain.corridor(point, point, level):
            break
        distance = length * step / steps
    return distance


def span_passed(position, origin, target, *, afloat=False):
    dx, dz = target[0] - origin[0], target[2] - origin[2]
    length = max(0.001, math.hypot(dx, dz))
    along = ((position[0] - target[0]) * dx + (position[2] - target[2]) * dz) / length
    across = abs((position[0] - origin[0]) * dz - (position[2] - origin[2]) * dx) / length
    height = abs(position[1] - target[1]) < (1.4 if afloat else 0.3)
    return height and -0.08 <= along <= 3 and across < 0.6


NATIVE_WALK_LEASE = r"""
import minescript as ms
Math = JavaClass("java.lang.Math")
active, aborted, floating, generation, timer, slowing = False, False, False, 0, None, False

def brake():
    global active
    if active:
        ms.player_press_forward(False)
    active = False

def timeout(expected):
    if expected == generation:
        brake()
        if not floating:
            ms.player_press_jump(False)

def drive(milliseconds, wet, slow=False, origin_x=0.0, origin_z=0.0, budget=-1.0):
    global active, floating, generation, timer, slowing
    if aborted:
        return -1
    if budget >= 0:
        position = ms.player_position()
        traveled = Math.sqrt((position[0]-origin_x)**2+(position[2]-origin_z)**2)
        remaining = budget-traveled
        if remaining < 0.25:
            stop()
            ms.player_press_sneak(not wet)
            slowing = True
            return 0
        if remaining < 0.8 and not slowing:
            stop()
            ms.player_press_sneak(not wet)
            slowing = True
            return 0
        slow = slow or remaining < 1.2
        margin,speed = (0.15,3) if wet else (0.15,2) if slow else (0.65,7)
        milliseconds = min(milliseconds,max(30,int((remaining-margin)/speed*1000)))
    generation += 1
    if timer is not None:
        ms.remove_event_listener(timer)
    floating = wet
    slowing = slow or wet
    ms.player_press_sneak(slow and not wet)
    if not active:
        ms.player_press_forward(True)
        active = True
    timer = ms.set_timeout(timeout, JavaInt(milliseconds), generation)
    return 1

def stop():
    global generation, timer
    generation += 1
    if timer is not None:
        ms.remove_event_listener(timer)
        timer = None
    brake()
    ms.player_press_sneak(False)

def abort():
    global aborted
    aborted = True
    stop()
    ms.player_press_jump(False)

def key(event):
    if event.key == 297 and event.action == 1:
        abort()

def tick(event):
    if active and ms.screen_name() is not None:
        abort()

key_listener = ms.add_event_listener("key", key)
tick_listener = ms.add_event_listener("tick", tick)

def close():
    stop()
    ms.remove_event_listener(key_listener)
    ms.remove_event_listener(tick_listener)
"""


class WalkLease:
    """Release forward inside the game if Python exhausts its checked runway."""

    def __init__(self):
        from java import eval_pyjinn_script

        self.script: Any = eval_pyjinn_script(NATIVE_WALK_LEASE)
        self._drive: Any = self.script.get("drive")
        self.stop: Any = self.script.get("stop")
        self._close: Any = self.script.get("close")

    def drive(self, distance, wet=False, *, origin=None):
        # Reserve room for the player's width and residual ground momentum.
        # The time cap also bounds an interrupted or stalled Python process.
        milliseconds = walk_budget(distance)
        result = self._drive(
            milliseconds,
            wet,
            distance < 1.2,
            origin[0] if origin is not None else 0.0,
            origin[2] if origin is not None else 0.0,
            distance if origin is not None else -1.0,
        )
        if result < 0:
            raise Stopped("Walking stopped with F8 or an open menu.")
        return result > 0

    def close(self):
        try:
            self._close()
        finally:
            self.script.exit()


def walk_budget(distance):
    slow = distance < 1.2
    return max(
        60, min(1500, int(max(0, distance - (0.15 if slow else 0.65)) / (2 if slow else 7) * 1000))
    )


def move(session, start, end, *, walker=None, continuation=(), afloat=False):
    """One continuous step/jump; accept forward progress instead of recentering."""
    owned = walker is None
    walker = Walker(session) if owned else walker
    walker.float(afloat)
    runway, previous = [], end
    for point in continuation:
        if point[1] != end[1] or heading(previous, point) != heading(start, end):
            break
        runway.append(point)
        previous = point
    target = runway[-1] if runway else end
    aim = (target[0] + 0.5, target[1], target[2] + 0.5)
    began, next_check, jumped, success = time.monotonic(), 0.0, False, False
    try:
        while time.monotonic() - began < 5:
            session.check()
            px, py, pz = session.position
            grounded = session.client.grounded()
            if (
                abs(py - end[1]) < 0.3
                and (grounded or afloat)
                and (
                    (math.floor(px), math.floor(pz)) == (end[0], end[2])
                    or passed(session.position, start, end)
                )
            ):
                success = True
                return True
            if (
                py < min(start[1], end[1]) - (1.4 if afloat else 0.4)
                or math.hypot(px - aim[0], pz - aim[2]) > 5
            ):
                raise Stopped("Player left the checked step. Take control.")
            if jumped and grounded and py < end[1] - 0.2 and time.monotonic() - began > 1.2:
                return False
            if time.monotonic() >= next_check:
                if not recheck_edges(start, [end, *runway]):
                    return False
                body = corridor_terrain(session.position, aim, start[1], end[1])
                if not all(
                    any(body.traversable((x, level, z)) for level in {start[1], end[1]})
                    for x, z in swept_cells(session.position, aim)
                ):
                    return False
                next_check = time.monotonic() + 0.12
            if session.eat(stay_afloat=afloat):
                walker.stop()
            m.player_look_at(aim[0], py + 1.62, aim[2])
            if walker.lease is None:
                walker.lease = WalkLease()
            if not afloat and end[1] > start[1] and not jumped and grounded:
                m.player_press_jump(True)
                jumped = True
            elif not afloat and jumped and not grounded:
                release("jump")
            crossed = span_passed(
                session.position,
                (start[0] + 0.5, py, start[2] + 0.5),
                (end[0] + 0.5, py, end[2] + 0.5),
            )
            if crossed and not runway and not grounded:
                walker.stop()
            else:
                walker.drive(math.hypot(aim[0] - px, aim[2] - pz) + 0.3, afloat)
            time.sleep(0.03)
        return False
    finally:
        if not afloat:
            release("jump")
        if owned:
            walker.close()
        elif not success or not runway:
            walker.stop()


def heading(start, end):
    return end[0] - start[0], end[2] - start[2]


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
        self.lease = None

    def float(self, enabled):
        if self.floating != enabled:
            m.player_press_jump(enabled)
            if enabled:
                release("sprint")
            self.floating = enabled

    def surface(self):
        if self.walking:
            if self.lease is not None:
                self.lease.stop()
            else:
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
        if self.lease is not None:
            self.lease.stop()
        if self.walking or self.floating:
            release("jump")
            if self.lease is None:
                release("forward")
            self.walking = False
            self.floating = False

    def drive(self, distance, wet=False):
        if self.lease is None:
            self.lease = WalkLease()
        self.walking = self.lease.drive(distance, wet, origin=self.session.position)
        return self.walking

    def close(self):
        self.stop()
        if self.lease is not None:
            self.lease.close()
            self.lease = None

    def reserve(self, position, point, level, destination, wet):
        dx, dz = point[0] - position[0], point[2] - position[2]
        length = math.hypot(dx, dz)
        distance = min(6, destination.distance(position))
        if length < 0.01 or distance < 1:
            return False
        runway = (position[0] + dx / length * distance, level, position[2] + dz / length * distance)
        fresh = corridor_terrain(position, runway, level)
        sampled = time.monotonic()
        self.session.check(force=True)
        position = self.session.position
        if not fresh.corridor(position, runway, level):
            return False
        distance = math.hypot(runway[0] - position[0], runway[2] - position[2])
        m.player_look_at(runway[0], position[1] + 1.62, runway[2])
        distance -= 7 * (time.monotonic() - sampled)
        if distance < 0.8:
            self.stop()
            return False
        return self.drive(distance, wet)

    def follow(self, start, path, destination=None, *, refresh=False, planned=None):
        """Follow committed, body-width checked spans; progress never chases old centers."""
        completed, active, next_check = [], None, 0.0
        if self.lease is None:
            self.lease = WalkLease()
        terrain = planned if planned is not None else Terrain.scan(start)
        last_position, last_progress = self.session.position, time.monotonic()
        while path:
            self.session.check()
            position = self.session.position
            in_water = self.session.client.in_water()
            if in_water and (self.session.client.underwater() or position[1] < start[1] - 0.9):
                self.surface()
                active = None
                continue
            if destination is not None and arrived(destination, position, afloat=in_water):
                self.stop()
                return completed, False
            if math.hypot(position[0] - last_position[0], position[2] - last_position[2]) > 0.05:
                last_position, last_progress = position, time.monotonic()
            elif time.monotonic() - last_progress > 3:
                self.stop()
                return completed, True
            if active is None:
                end = path[0]
                wet = in_water or terrain.swimmable(start) or terrain.swimmable(end)
                self.float(wet)
                if end[1] != start[1]:
                    if not move(
                        self.session, start, end, walker=self, continuation=path[1:3], afloat=wet
                    ):
                        self.stop()
                        return completed, True
                    completed.append(end)
                    start, path = end, path[1:]
                    last_progress = time.monotonic()
                    continue
                index = shortcut(position, start, path, terrain)
                if index is None:
                    # No body-width corridor from the actual position. Replan
                    # there instead of turning back to a previous cell center.
                    self.stop()
                    return completed, True
                end = path[index]
                target = (end[0] + 0.5, end[1], end[2] + 0.5)
                active = (position, target, index, wet)
                next_check = 0
            origin, target, index, wet = active
            distance = math.hypot(position[0] - target[0], position[2] - target[2])
            # On a clear continuation, advance the aim before reaching a short
            # waypoint. This preserves forward motion through arbitrary slopes
            # of X/Z direction rather than making one-cell staircase turns.
            early = (
                distance < 1.1
                and index + 1 < len(path)
                and path[index + 1][1] == target[1]
                and shortcut(position, path[index], path[index + 1 :], terrain) is not None
            )
            if (early or span_passed(position, origin, target, afloat=wet)) and (
                wet or self.session.client.grounded()
            ):
                completed.extend(path[: index + 1])
                start, path = path[index], path[index + 1 :]
                active = None
                if (
                    not path
                    and destination is not None
                    and destination.distance(position) <= 8
                    and (destination.y is None or abs(destination.y - start[1]) < 0.3)
                ):
                    goal = (math.floor(destination.x), start[1], math.floor(destination.z))
                    finish = (goal[0] + 0.5, goal[1], goal[2] + 0.5)
                    fresh = corridor_terrain(position, finish, start[1])
                    if fresh.corridor(position, finish, start[1]):
                        terrain.states.update(fresh.states)
                        path = [goal]
                        continue
                if (
                    refresh
                    and destination is not None
                    and destination.distance(position) > 8
                    and (len(completed) >= 4 or not path)
                ):
                    look = shortcut(position, start, path, terrain, distance=10) if path else None
                    point = (
                        (path[look][0] + 0.5, start[1], path[look][2] + 0.5)
                        if look is not None
                        else (destination.x, start[1], destination.z)
                        if not path
                        else None
                    )
                    if point is not None and self.reserve(
                        position, point, start[1], destination, wet
                    ):
                        return completed, False
                continue
            if position[1] < min(start[1], target[1]) - 1.4:
                raise Stopped("Player dropped below the checked route. Take control.")
            if not wet and abs(position[1] - target[1]) > 0.4:
                self.stop()
                return completed, False
            if (
                not in_water
                and not terrain.swimmable((math.floor(target[0]), target[1], math.floor(target[2])))
                and terrain.standable(
                    (math.floor(position[0]), round(position[1]), math.floor(position[2]))
                )
            ):
                self.float(False)
            if self.session.eat(stay_afloat=wet):
                self.stop()
                self.session.check(force=True)
                last_position, last_progress = self.session.position, time.monotonic()
                active = None
                continue
            if time.monotonic() >= next_check:
                dx, dz = target[0] - position[0], target[2] - position[2]
                length = max(0.001, math.hypot(dx, dz))
                extent = max(5, length)
                ray = (
                    position[0] + dx / length * extent,
                    target[1],
                    position[2] + dz / length * extent,
                )
                fresh = corridor_terrain(position, ray, target[1])
                terrain.states.update(fresh.states)
                sampled = time.monotonic()
                self.session.check(force=True)
                position = self.session.position
                if span_passed(position, origin, target, afloat=wet):
                    next_check = 0
                    continue
                if not fresh.corridor(position, target, target[1]):
                    self.stop()
                    return completed, True
                dx, dz = target[0] - position[0], target[2] - position[2]
                length = max(0.001, math.hypot(dx, dz))
                ray = (position[0] + dx / length * 5, target[1], position[2] + dz / length * 5)
                budget = safe_runway(fresh, position, ray, target[1])
                if budget < 0.25:
                    self.stop()
                    return completed, True
                m.player_look_at(target[0], position[1] + 1.62, target[2])
                budget -= 7 * (time.monotonic() - sampled)
                if budget < 0.25:
                    self.stop()
                    return completed, False
                if not self.drive(budget, wet):
                    return completed, False
                next_check = time.monotonic() + 0.12
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
    m.echo(f"Walking destination: {destination.describe()}.")
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
                terrain = Terrain.scan(current)
                path = plan(terrain, current, destination, recent)
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
                    if actual in path:
                        path = path[path.index(actual) + 1 :]
                    elif shortcut(session.position, actual, path, terrain) is None:
                        walker.stop()
                        continue
                    current = actual
                    if not path:
                        walker.stop()
                        continue
                completed, blocked = walker.follow(
                    current, path, destination, refresh=True, planned=terrain
                )
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
            walker.close()
        m.echo("Arrived at the walking destination.")


if __name__ == "__main__":
    run(main)
