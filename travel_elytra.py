# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
r"""Rocket-assisted flight: \travel_elytra X Z or X Y Z [--height 50] [--check].

Wear an Elytra, carry plain rockets and ordinary food. Clear outdoor takeoff
and a dry landing area are required. F8 releases controls, NOT momentum.
"""

import math
import re
import time
from typing import Any, Callable

import minescript as m

from travel import Terrain, passable
from travel import main as walk_main
from travel_common import (
    Client,
    Destination,
    NoFood,
    Session,
    Stopped,
    arguments,
    exclusive,
    field,
    item_id,
    release,
    run,
    select_item,
    usable_items,
)


def rockets():
    return [
        item
        for item in usable_items()
        if item_id(item) == "firework_rocket"
        and not re.search(
            r"explosions[\"']?\s*[:=]\s*\[\s*[^\s\]]",
            str(field(item, "nbt", "")).casefold(),
        )
    ]


# Critical launch actions run together on a game tick. Separate Python/Java RPCs
# used to consume most of the jump before the first rocket could be used.
NATIVE_FLIGHT = r"""
import minescript as ms
Minecraft = JavaClass("net.minecraft.client.Minecraft")
Packet = JavaClass("net.minecraft.network.protocol.game.ServerboundPlayerCommandPacket")
Action = JavaClass("net.minecraft.network.protocol.game.ServerboundPlayerCommandPacket$Action")
Hand = JavaClass("net.minecraft.world.InteractionHand")
Items = JavaClass("net.minecraft.world.item.Items")
Components = JavaClass("net.minecraft.core.component.DataComponents")
Heightmap = JavaClass("net.minecraft.world.level.levelgen.Heightmap$Types")
mc = Minecraft.getInstance()
player, level = mc.player, mc.level
status, ticks, listener, key_listener = 0, 0, None, None
health = player.getHealth()

def ready():
    return (mc.player == player and mc.level == level and mc.screen is None
            and player.getHealth() >= health and player.getHealth() > 6)

def burn():
    if not ready() or player.onGround() or not player.isFallFlying():
        return 0.0
    stack = player.getMainHandItem()
    if not stack.getItem().equals(Items.FIREWORK_ROCKET):
        return 0.0
    component = stack.get(Components.FIREWORKS)
    duration = 1
    if component is not None:
        if not component.explosions().isEmpty():
            return 0.0
        duration = component.flightDuration()
    if not mc.gameMode.useItem(player, Hand.MAIN_HAND).consumesAction():
        return 0.0
    # Maximum vanilla lifetime, including the random extension, plus a margin.
    return (10 * (1 + duration) + 13) / 20.0 + 0.5

def cancel():
    global status
    status = -2
    ms.player_press_jump(False)

def key(event):
    if event.key == 297 and event.action == 1:
        cancel()

def tick(event):
    global status, ticks
    if status != 0:
        return
    ticks += 1
    if not ready():
        cancel()
        return
    if ticks > 40:
        status = -1
        ms.player_press_jump(False)
        return
    if player.onGround():
        return
    ms.player_press_jump(False)
    if not player.isFallFlying():
        if not player.tryToStartFallFlying():
            return
        player.connection.send(Packet(player, Action.START_FALL_FLYING))
    lifetime = burn()
    status = lifetime if lifetime > 0 else -1

def arm():
    global listener, key_listener
    key_listener = ms.add_event_listener("key", key)
    listener = ms.add_event_listener("tick", tick)
    if player.onGround():
        ms.player_press_jump(True)

def stop():
    global status
    if status == 0:
        status = -2
    ms.player_press_jump(False)
    if listener is not None:
        ms.remove_event_listener(listener)
    if key_listener is not None:
        ms.remove_event_listener(key_listener)

def surfaces(x, z, radius):
    rows = []
    for dx in range(-radius, radius + 1, 4):
        for dz in range(-radius, radius + 1, 4):
            px, pz = x + dx, z + dz
            if level.hasChunk(px >> 4, pz >> 4):
                y = level.getHeight(Heightmap.MOTION_BLOCKING_NO_LEAVES, px, pz)
                if y > level.getMinY():
                    rows.append(f"{px},{y},{pz}")
    return ";".join(rows)
"""


class NativeFlight:
    def __init__(self):
        from java import eval_pyjinn_script

        self.script: Any = eval_pyjinn_script(NATIVE_FLIGHT)
        self.burn: Callable[[], float] = self.script.get("burn")
        self.arm: Callable[[], None] = self.script.get("arm")
        self.stop: Callable[[], None] = self.script.get("stop")
        self.surfaces: Callable[[int, int, int], str] = self.script.get("surfaces")

    def status(self):
        return float(self.script.get("status"))

    def close(self):
        try:
            self.stop()
        finally:
            self.script.exit()


def landing_area(destination, position, native=None):
    """Check small dry pads across a wider area, without scanning entire columns."""
    gx, gz = math.floor(destination.x), math.floor(destination.z)
    if native is None:
        if destination.y is None:
            raise Stopped("Surface lookup is unavailable. Take control of the flight.")
        candidates = [
            (gx + dx, round(destination.y), gz + dz)
            for dx in range(-24, 25, 4)
            for dz in range(-24, 25, 4)
        ]
    else:
        rows = native.surfaces(gx, gz, 24)
        candidates = [tuple(map(int, row.split(","))) for row in rows.split(";") if row]
        if destination.y is not None:
            candidates = [p for p in candidates if abs(p[1] - destination.y) <= 0.5]
    candidates = sorted(candidates, key=lambda p: (p[0] - gx) ** 2 + (p[2] - gz) ** 2)
    candidates = [p for p in candidates if p[1] <= position[1] + 2]
    positions = list(
        dict.fromkeys(
            (x + dx, y + dy, z + dz)
            for x, y, z in candidates
            for dx in range(-2, 3)
            for dz in range(-2, 3)
            for dy in (-1, 0, 1, 2)
        )
    )
    if positions:
        terrain = Terrain(
            dict(zip(positions, m.getblocklist([list(p) for p in positions]), strict=True))
        )
        for x, y, z in candidates:
            if all(
                terrain.standable((x + dx, y, z + dz)) for dx in range(-2, 3) for dz in range(-2, 3)
            ):
                return Destination(x + 0.5, z + 0.5, y)
    raise Stopped("No dry, clear landing surface found within 24 blocks. Take over the flight.")


def glide_step(velocity, yaw, pitch):
    """Predict one unboosted vanilla tick, using ordinary gravity and no effects."""
    yaw, pitch = math.radians(yaw), math.radians(pitch)
    hx, hz = -math.sin(yaw), math.cos(yaw)
    vx, vy, vz = velocity
    speed = math.hypot(vx, vz)
    lift = math.cos(pitch) ** 2
    vy += 0.08 * (-1 + lift * 0.75)
    if vy < 0:
        recovery = -vy * 0.1 * lift
        vx, vy, vz = vx + hx * recovery, vy + recovery, vz + hz * recovery
    if pitch < 0:
        recovery = speed * -math.sin(pitch) * 0.04
        vx, vy, vz = vx - hx * recovery, vy + recovery * 3.2, vz - hz * recovery
    vx += (hx * speed - vx) * 0.1
    vz += (hz * speed - vz) * 0.1
    return vx * 0.99, vy * 0.98, vz * 0.99


def landing_angles(position, velocity, destination):
    """Choose an approach from predicted motion, including braking before contact.

    This deliberately models several seconds rather than aiming the camera at
    the pad: Elytra momentum does not turn instantly with the camera.
    """
    dx, dz = destination.x - position[0], destination.z - position[2]
    direct = math.degrees(math.atan2(-dx, dz))
    heading = math.degrees(math.atan2(-velocity[0], velocity[2]))
    best = (math.inf, direct, 0)
    for yaw in (direct, direct - 45, direct + 45, heading + 90, heading - 90, heading + 180):
        for pitch in (-65, -45, -25, -10, 0, 15, 30, 45):
            x, y, z = position
            predicted = velocity
            for _ in range(100):
                old_y, old_x, old_z = y, x, z
                predicted = glide_step(predicted, yaw, pitch)
                x, y, z = x + predicted[0], y + predicted[1], z + predicted[2]
                if y <= destination.y:
                    fraction = (old_y - destination.y) / max(0.001, old_y - y)
                    x, z = old_x + predicted[0] * fraction, old_z + predicted[2] * fraction
                    break
            horizontal = math.hypot(predicted[0], predicted[2])
            cost = (x - destination.x) ** 2 + (z - destination.z) ** 2
            cost += max(0, y - destination.y) ** 2 * 0.8
            cost += horizontal**2 * 180 + predicted[1] ** 2 * 300
            if y <= destination.y and (horizontal > 0.55 or predicted[1] < -0.5):
                cost += 10_000
            if cost < best[0]:
                best = cost, yaw, pitch
    return best[1], best[2]


def flight_angles(position, velocity, destination, cruise_y, landing=False):
    dx, dz = destination.x - position[0], destination.z - position[2]
    yaw = math.degrees(math.atan2(-dx, dz))
    if not landing:
        return yaw, -2
    return landing_angles(position, velocity, destination)


class Flight:
    def __init__(self, session, destination, height):
        self.session, self.destination = session, destination
        self.cruise_y = min(
            310,
            max(
                session.position[1] + height,
                (destination.y if destination.y is not None else session.position[1]) + height,
            ),
        )
        self.landing = None
        self.fallback = False
        self.last_boost = -math.inf
        self.next_scan = self.next_steer = self.next_wings = 0.0
        self.remaining_wings = 0
        self.native = None
        self.boost_until = 0.0
        self.climbing = False
        self.rockets_used = 0

    def prepare_rocket(self):
        available = rockets()
        if not available:
            return None
        previous = select_item(available[0])
        if item_id(field(m.player_hand_items(), "main_hand")) != "firework_rocket":
            m.player_inventory_select_slot(previous)
            raise Stopped("Rocket did not appear in your hand. Check your inventory.")
        return previous

    def boost(self):
        if not self.session.client.flying():
            raise Stopped("Elytra is not gliding; no rocket was used.")
        if time.monotonic() < self.boost_until:
            return False
        previous = self.prepare_rocket()
        if previous is None:
            return False
        try:
            self.session.check()
            if self.native is None:
                self.native = NativeFlight()
            yaw, _ = flight_angles(
                self.session.position, self.session.velocity, self.destination, self.cruise_y
            )
            m.player_set_orientation(yaw, -55)
            duration = self.native.burn()
        finally:
            m.player_inventory_select_slot(previous)
        if not duration:
            raise Stopped("Minecraft refused the rocket use. Take control of the flight.")
        self.last_boost = time.monotonic()
        self.boost_until = self.last_boost + duration
        self.climbing = True
        self.rockets_used += 1
        return True

    def takeoff(self):
        if self.session.client.flying():
            return
        if self.session.client.creative_flying():
            raise Stopped("Creative flight is active. Land and turn it off before Elytra takeoff.")
        x, y, z = (math.floor(value) for value in self.session.position)
        positions = [
            [x + dx, y + dy, z + dz]
            for dx in (-1, 0, 1)
            for dz in (-1, 0, 1)
            for dy in range(2, 10)
        ]
        dx = self.destination.x - self.session.position[0]
        dz = self.destination.z - self.session.position[2]
        distance = max(0.01, math.hypot(dx, dz))
        positions.extend(
            [
                math.floor(self.session.position[0] + dx / distance * ahead),
                y + up,
                math.floor(self.session.position[2] + dz / distance * ahead),
            ]
            for ahead in range(1, 9)
            for up in range(1, 7)
        )
        if not all(passable(state) for state in m.getblocklist(positions)):
            raise Stopped(
                "Takeoff needs clear space overhead. Move outside, away from trees/buildings."
            )
        if self.session.client.grounded():
            self.session.eat()
        self.native = NativeFlight()
        self.session.check()
        yaw, _ = flight_angles(
            self.session.position, self.session.velocity, self.destination, self.cruise_y
        )
        m.player_set_orientation(yaw, -55)
        previous = self.prepare_rocket()
        if previous is None:
            raise Stopped("No plain flight rockets left. Take control.")
        try:
            self.session.check()
            self.native.arm()
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                self.session.check()
                status = self.native.status()
                if status > 0:
                    self.last_boost = time.monotonic()
                    self.boost_until = self.last_boost + status
                    self.climbing = True
                    self.rockets_used += 1
                    return
                if status < 0:
                    break
                self.session.wait(0.05)
            if self.session.client.grounded():
                raise Stopped("Jump did not leave the ground. Check the ceiling, water or riding.")
            raise Stopped("Minecraft refused the glide or rocket. Take control of the flight.")
        finally:
            self.native.stop()
            release("jump")
            m.player_inventory_select_slot(previous)

    def close(self):
        if self.native is not None:
            self.native.close()

    def obstacles(self):
        position, velocity = self.session.position, self.session.velocity
        speed = math.hypot(velocity[0], velocity[2])
        if speed < 0.05:
            yaw = math.radians(m.player_orientation()[0])
            heading = -math.sin(yaw), math.cos(yaw)
        else:
            heading = velocity[0] / speed, velocity[2] / speed
        samples = []
        for distance in (4, 8, 16, 24, 36):
            x = math.floor(position[0] + heading[0] * distance)
            z = math.floor(position[2] + heading[1] * distance)
            for dy in (0, 1, 2):
                samples.append((distance, [x, math.floor(position[1]) + dy, z]))
        states = m.getblocklist([pos for _, pos in samples])
        blocked = [
            distance
            for (distance, _), state in zip(samples, states, strict=True)
            if not passable(state)
        ]
        if blocked:
            if min(blocked) <= 8:
                raise Stopped(
                    "Obstacle immediately ahead. Travel controls released: take over the flight."
                )
            self.cruise_y = min(310, max(self.cruise_y, position[1] + 20))
            return True
        return False

    def steer(self):
        now = time.monotonic()
        if now < self.next_steer:
            return
        self.next_steer = now + 0.12
        self.session.check()
        if not self.session.client.flying():
            if self.landing is not None and self.session.client.grounded():
                return
            raise Stopped("Gliding ended unexpectedly. Travel controls released.")
        avoiding = False
        if now >= self.next_scan:
            avoiding = self.obstacles()
            self.next_scan = now + 0.3
        target = self.landing or self.destination
        yaw, pitch = flight_angles(
            self.session.position,
            self.session.velocity,
            target,
            self.cruise_y,
            self.landing is not None,
        )
        if self.landing is None and self.climbing:
            if now < self.boost_until:
                pitch = -55 if self.session.position[1] < 300 else 0
            elif self.session.velocity[1] > 0.05:
                pitch = -15
            else:
                self.climbing = False
        if avoiding:
            if self.landing is not None:
                raise Stopped("Landing approach obstructed. Take control of the flight.")
            pitch = -40
        m.player_set_orientation(yaw, pitch)

    def begin_landing(self, *, fallback=False):
        # The approach model is unboosted: let an existing rocket finish first.
        if time.monotonic() < self.boost_until:
            self.session.wait(self.boost_until - time.monotonic(), on_tick=self.steer)
            self.session.check(force=True)
        target = self.destination
        if fallback:
            target = Destination(self.session.position[0], self.session.position[2])
        if self.native is None:
            self.native = NativeFlight()
        try:
            self.landing = landing_area(target, self.session.position, self.native)
        except Stopped:
            # A tree/building at the exact goal must not discard an otherwise
            # flyable route. Try a loaded surface underneath the current flight.
            target = Destination(self.session.position[0], self.session.position[2])
            self.landing = landing_area(target, self.session.position, self.native)
            fallback = True
        self.fallback = fallback
        m.echo("Landing approach: rockets off. Preparing to finish on foot.")

    def fly(self):
        self.takeoff()
        report_at, landing_started = 0.0, None
        while True:
            self.session.check()
            if self.landing is not None and self.session.client.grounded():
                if abs(self.session.position[1] - self.landing.y) > 1:
                    raise Stopped(
                        "Touched ground outside the landing level. Check your surroundings."
                    )
                m.echo("Landed. Continuing toward the requested coordinates on foot.")
                return
            now = time.monotonic()
            distance = self.destination.distance(self.session.position)
            if now >= self.next_wings:
                self.remaining_wings = self.session.client.wings_remaining()
                self.next_wings = now + 2
            if self.landing is None:
                if self.remaining_wings <= 60 or not rockets():
                    self.begin_landing(fallback=True)
                    landing_started = now
                elif distance <= max(
                    160,
                    2
                    * (
                        self.session.position[1]
                        - (self.destination.y if self.destination.y is not None else 64)
                    ),
                ):
                    self.begin_landing()
                    landing_started = now
            self.steer()
            if self.landing is None:
                if self.needs_boost(now):
                    self.boost()
                # Keep steering and checking the flight while eating; stopping
                # movement keys alone cannot stop an airborne player's momentum.
                try:
                    self.session.eat(on_tick=self.steer)
                except NoFood:
                    m.echo("Food depleted: attempting a landing before returning control.")
                    self.begin_landing(fallback=True)
                    landing_started = now
            elif landing_started is not None and now - landing_started > 90:
                raise Stopped("Landing has not completed after 90 seconds. Take control.")
            if now >= report_at:
                m.echo(
                    f"Flight: {distance:.0f} blocks away; {self.rockets_used} rockets used; "
                    f"Elytra durability {self.remaining_wings}."
                )
                report_at = now + 15
            self.session.wait(0.08)

    def needs_boost(self, now):
        # Fuel-saving default: spend altitude on a shallow glide, then climb on
        # one rocket. A timer alone never triggers a boost.
        return (
            self.landing is None
            and not self.climbing
            and now >= self.boost_until
            and self.session.position[1] < self.cruise_y - 25
            and self.session.velocity[1] <= 0.05
        )


def main(args):
    options = arguments(args, flight=True)
    exclusive()
    client = Client()
    remaining = client.wings_remaining()
    if remaining <= 60:
        raise Stopped("Elytra needs more than 60 durability remaining before a flight.")
    available = rockets()
    if not available:
        raise Stopped("Carry plain firework rockets without explosion stars in your inventory.")
    if options.check:
        m.echo(
            f"Flight check: hunger {client.food_level()}/20; Elytra durability {remaining}; "
            f"{sum(field(item, 'count', 0) for item in available)} plain rockets."
        )
        m.echo("Read-only check complete. Takeoff/landing terrain is checked during travel.")
        m.echo(
            f"Launch state: on ground={client.grounded()}, Elytra gliding={client.flying()}, "
            f"Creative flight={client.creative_flying()}."
        )
        return
    if options.destination.reached(m.player_position()):
        m.echo("Already at the destination.")
        return
    with Session(client, options.eat_at) as session:
        flight = Flight(session, options.destination, options.height)
        try:
            flight.fly()
        finally:
            flight.close()
    # Reuse the walking engine for the final meters or if fuel/wings ran low.
    destination = options.destination
    coordinates = [f"{destination.x:.17g}", f"{destination.z:.17g}"]
    if destination.y is not None:
        coordinates.insert(1, f"{destination.y:.17g}")
    walk_main([*coordinates, "--eat-at", str(options.eat_at)])


if __name__ == "__main__":
    run(main)
