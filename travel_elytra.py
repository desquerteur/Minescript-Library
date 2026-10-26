# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
r"""Rocket-assisted flight: \travel_elytra X Z or X Y Z [--height 50] [--check].

Wear an Elytra, carry plain rockets and ordinary food. Clear outdoor takeoff
and a broad flat landing area are required. F8 releases controls, NOT momentum.
"""

import math
import re
import time

import minescript as m

from travel import Terrain, cell, passable
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


def landing_area(destination, position):
    """Find a flat 9x9 area near the requested point, entirely in loaded data."""
    gx, gz = math.floor(destination.x), math.floor(destination.z)
    # Explicit Y is respected; X Z chooses a visible safe surface below the flight.
    levels = (
        [round(destination.y)]
        if destination.y is not None
        else range(min(319, math.floor(position[1]) + 2), -64, -1)
    )
    positions = [
        (x, y, z)
        for x in range(gx - 8, gx + 9)
        for z in range(gz - 8, gz + 9)
        for y in range(min(levels) - 1, max(levels) + 3)
    ]
    terrain = Terrain(
        dict(zip(positions, m.getblocklist([list(pos) for pos in positions]), strict=True))
    )
    offsets = sorted(
        ((x, z) for x in range(-4, 5) for z in range(-4, 5)),
        key=lambda offset: offset[0] ** 2 + offset[1] ** 2,
    )
    for dx, dz in offsets:
        x, z = gx + dx, gz + dz
        for y in levels:
            if all(
                terrain.standable((x + ox, y, z + oz)) for ox in range(-4, 5) for oz in range(-4, 5)
            ):
                return Destination(x + 0.5, z + 0.5, y)
    raise Stopped("No flat, clear 9x9 landing area near the destination. Take over the flight.")


def flight_angles(position, velocity, destination, cruise_y, landing=False):
    dx, dz = destination.x - position[0], destination.z - position[2]
    distance = math.hypot(dx, dz)
    yaw = math.degrees(math.atan2(-dx, dz))
    if not landing:
        pitch = math.degrees(math.atan2(position[1] - cruise_y, 35))
        return yaw, max(-35, min(5, pitch))
    height = position[1] - destination.y
    speed = math.hypot(velocity[0], velocity[2])
    if height < 6 and speed > 0.35:
        # Flare to shed speed before touching down; never boost on approach.
        return yaw, -25
    pitch = math.degrees(math.atan2(height, max(distance, 12)))
    return yaw, max(-15, min(10 if height > 6 else 5, pitch))


class Flight:
    def __init__(self, session, destination, height):
        self.session, self.destination = session, destination
        self.cruise_y = min(
            310, max(session.position[1] + height, (destination.y or session.position[1]) + height)
        )
        self.landing = None
        self.fallback = False
        self.last_boost = -math.inf
        self.next_scan = self.next_steer = self.next_wings = 0.0
        self.remaining_wings = 0

    def boost(self):
        if not self.session.client.flying():
            raise Stopped("Elytra is not gliding; no rocket was used.")
        available = rockets()
        if not available:
            return False
        previous = select_item(available[0])
        try:
            m.player_press_use(True)
            self.session.wait(0.08)
        finally:
            release("use")
            m.player_inventory_select_slot(previous)
        self.last_boost = time.monotonic()
        return True

    def takeoff(self):
        if self.session.client.flying():
            return
        if not self.session.client.grounded():
            raise Stopped("Start on the ground or while already gliding.")
        x, y, z = cell(self.session.position)
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
        self.session.eat()
        yaw, _ = flight_angles(
            self.session.position, self.session.velocity, self.destination, self.cruise_y
        )
        m.player_set_orientation(yaw, -35)
        try:
            m.player_press_jump(True)
            self.session.wait(0.18)
            m.player_press_jump(False)
            self.session.wait(0.18)
            m.player_press_jump(True)
            self.session.wait(0.12)
        finally:
            release("jump")
        self.session.wait(0.12)
        if not self.session.client.flying():
            raise Stopped(
                "Elytra did not open. No rocket was used; check launch clearance and wings."
            )
        if not self.boost():
            raise Stopped("No plain flight rockets left. Take control.")

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
        if avoiding:
            if self.landing is not None:
                raise Stopped("Landing approach obstructed. Take control of the flight.")
            pitch = -40
        m.player_set_orientation(yaw, pitch)

    def begin_landing(self, *, fallback=False):
        target = self.destination
        if fallback:
            target = Destination(self.session.position[0], self.session.position[2])
        self.landing = landing_area(target, self.session.position)
        self.fallback = fallback
        m.echo("Landing approach: rockets off. Preparing to finish on foot.")

    def fly(self):
        self.takeoff()
        report_at, landing_started = 0.0, None
        while True:
            self.session.check(force=True)
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
                elif distance <= max(100, self.cruise_y - (self.destination.y or 64) + 30):
                    self.begin_landing()
                    landing_started = now
            self.steer()
            if self.landing is None:
                if now - self.last_boost >= 4:
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
                    f"Flight: {distance:.0f} blocks away; Elytra durability {self.remaining_wings}."
                )
                report_at = now + 15
            self.session.wait(0.08)


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
        return
    if options.destination.reached(m.player_position()):
        m.echo("Already at the destination.")
        return
    with Session(client, options.eat_at) as session:
        flight = Flight(session, options.destination, options.height)
        flight.fly()
    # Reuse the walking engine for the final meters or if fuel/wings ran low.
    walk_main([*options.coordinates, "--eat-at", str(options.eat_at)])


if __name__ == "__main__":
    run(main)
