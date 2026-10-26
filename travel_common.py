# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Shared food, coordinates and input cleanup for the two travel commands."""

import argparse
import logging
import math
import queue
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import minescript as m

# Ordinary foods only: no chorus fruit, poisonous food, golden apples or potions.
FOOD = {
    "cooked_beef": 8,
    "cooked_porkchop": 8,
    "cooked_mutton": 6,
    "cooked_salmon": 6,
    "cooked_chicken": 6,
    "golden_carrot": 6,
    "baked_potato": 5,
    "bread": 5,
    "cooked_rabbit": 5,
    "cooked_cod": 5,
    "apple": 4,
    "carrot": 3,
    "beetroot": 1,
    "potato": 1,
    "melon_slice": 2,
    "sweet_berries": 2,
    "glow_berries": 2,
    "cookie": 2,
    "dried_kelp": 1,
}


class Stopped(Exception):
    """A reason to stop and return control to the player."""


class NoFood(Stopped):
    """The flight controller can try to land before returning control."""


def field(value, name, default=None):
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def item_id(item):
    return str(field(item, "item", "")).removeprefix("minecraft:")


def usable_items():
    return [
        item
        for item in m.player_inventory()
        if field(item, "count", 0) > 0
        and field(item, "slot") is not None
        and 0 <= field(item, "slot") <= 35
    ]


def select_item(item):
    slot = field(item, "slot")
    if slot > 8:
        slot = m.player_inventory_slot_to_hotbar(slot)
    if not isinstance(slot, int) or not 0 <= slot <= 8:
        raise Stopped("Could not move the required item into the hotbar.")
    return m.player_inventory_select_slot(slot)


class Client:
    """Read live hunger/flight state using the installed Minescript Java bridge.

    Cache bound readers instead of repeatedly reflecting each field during flight.
    No game jars or third-party source are bundled with this project.
    """

    def __init__(self):
        from java import JavaClass

        minecraft_type: Any = JavaClass("net.minecraft.client.Minecraft")
        self.minecraft: Any = minecraft_type.getInstance()
        self.player: Any = self.minecraft.player
        if not self.player:
            raise Stopped("Join a world before starting travel.")
        self.hunger: Callable[[], int] = self.player.getFoodData().getFoodLevel
        self.grounded: Callable[[], bool] = self.player.onGround
        self.flying: Callable[[], bool] = self.player.isFallFlying
        self.chest_slot: Any = JavaClass("net.minecraft.world.entity.EquipmentSlot").CHEST
        self.elytra: Any = JavaClass("net.minecraft.world.item.Items").ELYTRA

    def food_level(self):
        level = self.hunger()
        if type(level) is not int or not 0 <= level <= 20:
            raise Stopped("Could not read hunger; travel has not assumed that you are fed.")
        return level

    def wings_remaining(self) -> int:
        chest: Any = self.player.getItemBySlot(self.chest_slot)
        if chest.isEmpty() or not chest.getItem().equals(self.elytra):
            raise Stopped("Equip an Elytra in your chest slot first.")
        maximum, damage = chest.getMaxDamage(), chest.getDamageValue()
        if type(maximum) is not int or type(damage) is not int or not 0 <= damage < maximum:
            raise Stopped("Elytra durability could not be read or the wings are broken.")
        return maximum - damage


@dataclass(frozen=True)
class Destination:
    x: float
    z: float
    y: float | None = None

    def distance(self, position):
        return math.hypot(self.x - position[0], self.z - position[2])

    def reached(self, position, radius=0.85):
        return self.distance(position) <= radius and (
            self.y is None or abs(self.y - position[1]) <= 0.3
        )


def coordinate(token, origin):
    value = origin + float(token[1:] or 0) if token.startswith("~") else float(token)
    if not math.isfinite(value):
        raise ValueError("Coordinates must be finite numbers.")
    return value


def arguments(args, *, flight=False):
    parser = argparse.ArgumentParser(
        prog="\\travel_elytra" if flight else "\\travel",
        description="Travel to X Z or X Y Z. Relative coordinates such as ~100 are supported.",
    )
    parser.add_argument("coordinates", nargs="+", metavar="COORD")
    parser.add_argument("--eat-at", type=int, default=14, metavar="POINTS")
    parser.add_argument("--check", action="store_true", help="Read-only setup and route check")
    if flight:
        parser.add_argument("--height", type=int, default=50, help="Cruise clearance in blocks")
    options = parser.parse_args(args)
    if len(options.coordinates) not in (2, 3):
        raise ValueError("Use X Z or X Y Z after the travel command.")
    if not 1 <= options.eat_at <= 19:
        raise ValueError("--eat-at must be between 1 and 19 hunger points (out of 20).")
    if flight and not 25 <= options.height <= 120:
        raise ValueError("--height must be between 25 and 120 blocks.")
    origin = m.player_position()
    if len(options.coordinates) == 3:
        x, y, z = [coordinate(t, o) for t, o in zip(options.coordinates, origin, strict=True)]
    else:
        x, z = [
            coordinate(t, o)
            for t, o in zip(options.coordinates, (origin[0], origin[2]), strict=True)
        ]
        y = None
    if max(abs(x), abs(z)) > 29_999_000 or y is not None and not -2048 <= y <= 2048:
        raise ValueError("Destination is outside supported world coordinates.")
    options.destination = Destination(x, z, y)
    return options


def exclusive():
    for job in m.job_info():
        if job.self or not job.command:
            continue
        name = Path(job.command[0].replace("\\", "/")).stem
        if name in {"travel", "travel_elytra"}:
            raise Stopped(f"Another traveler is active (job {job.job_id}). Stop it first.")


def release(*names):
    for name in names:
        try:
            getattr(m, "player_press_" + name)(False)
        except Exception as error:
            logging.getLogger(__name__).warning("Could not release %s: %s", name, error)


class Session:
    def __init__(self, client, eat_at=14):
        self.client, self.eat_at = client, eat_at
        self.events = m.EventQueue()
        self.position = None
        self.velocity = (0, 0, 0)
        self.health = None
        self.world = None
        self.next_snapshot = self.next_world = self.next_food = 0.0
        self.last_food = 20

    def __enter__(self):
        try:
            self.events.register_key_listener()
            start = time.monotonic()
            while m.screen_name() is not None:
                if time.monotonic() - start > 2:
                    raise Stopped("Close the chat or menu, then try again.")
                time.sleep(0.05)
            info = m.world_info()
            self.world = (info.name, info.address, info.dimension)
            self.check(force=True)
            m.echo("Travel started. F8 or opening chat/a menu releases travel controls.")
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def check(self, force=False):
        while True:
            try:
                event = self.events.get(block=False)
            except queue.Empty:
                break
            if field(event, "key") == 297 and field(event, "action") == 1:
                raise Stopped(
                    "Stopped with F8. Flight momentum continues: take control if airborne."
                )
        now = time.monotonic()
        if force or now >= self.next_snapshot:
            if m.screen_name() is not None:
                raise Stopped("Menu opened; travel controls released.")
            player = m.player()
            self.position = tuple(player.position)
            self.velocity = tuple(player.velocity)
            health = player.health if player.health is not None else m.player_health()
            if health <= 6 or self.health is not None and health < self.health:
                raise Stopped("Damage or low health detected. Take control.")
            self.health = health
            self.next_snapshot = now + 0.1
        if force or now >= self.next_world:
            info = m.world_info()
            if (info.name, info.address, info.dimension) != self.world:
                raise Stopped("World or dimension changed.")
            self.next_world = now + 1

    def wait(self, seconds, on_tick=None):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.check()
            if on_tick is not None:
                on_tick()
            time.sleep(min(0.05, max(0, end - time.monotonic())))

    def eat(self, on_tick=None):
        now = time.monotonic()
        if now < self.next_food:
            return False
        level = self.client.food_level()
        self.last_food = level
        self.next_food = now + 1
        if level > self.eat_at:
            return False
        release("forward", "jump", "sprint")
        m.echo(f"Hunger {level}/20: eating before continuing.")
        # Hunger must actually increase; consumption is not inferred from a timer.
        while level < max(18, self.eat_at + 1):
            foods = [item for item in usable_items() if item_id(item) in FOOD]
            if not foods:
                raise NoFood("No supported food left in your inventory. Take control.")
            food = max(foods, key=lambda item: FOOD[item_id(item)])
            previous = select_item(food)
            orientation = m.player_orientation() if on_tick is None else None
            try:
                self.wait(0.1, on_tick)
                if item_id(field(m.player_hand_items(), "main_hand")) != item_id(food):
                    raise Stopped(
                        "Selected food did not appear in your hand. Check your inventory."
                    )
                if orientation is not None:
                    # Do not open an interactive block instead of eating.
                    m.player_set_orientation(orientation[0], -65)
                started = time.monotonic()
                m.player_press_use(True)
                while self.client.food_level() <= level:
                    if time.monotonic() - started > 6:
                        raise Stopped(
                            "Eating did not restore hunger. Check food and game connection."
                        )
                    self.wait(0.15, on_tick)
                level = self.client.food_level()
            finally:
                release("use")
                m.player_inventory_select_slot(previous)
                if orientation is not None:
                    m.player_set_orientation(*orientation)
        self.last_food = level
        self.next_food = time.monotonic() + 1
        m.echo(f"Hunger {level}/20: continuing travel.")
        return True

    def __exit__(self, *unused):
        release("forward", "jump", "sprint", "use", "attack")
        try:
            self.events.unregister_all()
        except Exception as error:
            logging.getLogger(__name__).warning("Could not unregister stop listener: %s", error)


def run(main):
    try:
        main(sys.argv[1:])
    except (Stopped, ValueError) as error:
        m.echo(str(error))
