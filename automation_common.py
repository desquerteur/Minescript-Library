# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Shared timing and input cleanup for the automation commands."""

import logging
import math
import queue
import time

import minescript as m


class Stopped(Exception):
    """An expected reason for finishing an automation session."""


def duration(args, default=300):
    if len(args) > 1:
        raise ValueError("Provide at most one duration in seconds.")
    value = float(args[0]) if args else default
    if not math.isfinite(value) or not 1 <= value <= 3600:
        raise ValueError("Duration must be between 1 and 3600 seconds.")
    return value


def block_id(state):
    return state.split("[", 1)[0]


def held_item():
    item = m.player_hand_items().main_hand
    # Minescript 5.0's HandItems transform can leave nested items as dicts.
    if isinstance(item, dict):
        return item.get("item", "minecraft:air"), item.get("count", 0)
    return getattr(item, "item", "minecraft:air"), getattr(item, "count", 0)


def require_item(item_id):
    item, count = held_item()
    if item != item_id or count < 1:
        raise Stopped(f"Hold {item_id} in your main hand.")


class Session:
    """Stop on F8, a GUI, damage, world changes, or the time limit."""

    def __init__(self, seconds):
        self.deadline = time.monotonic() + seconds
        self.events = m.EventQueue()
        self.world = None
        self.health = 0.0

    def __enter__(self):
        try:
            self.events.register_key_listener()
            # The chat used to launch the command may still be closing.
            start = time.monotonic()
            while m.screen_name() is not None:
                if time.monotonic() - start >= 2:
                    raise Stopped("Close the chat or menu before starting.")
                time.sleep(0.05)
            info = m.world_info()
            self.world = (info.name, info.address, info.dimension)
            self.health = m.player_health()
            if self.health <= 6:
                raise Stopped("Health is too low to start automation.")
            m.echo("Started. F8 or opening a menu stops this script.")
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def check(self):
        while True:
            try:
                event = self.events.get(block=False)
            except queue.Empty:
                break
            if event.key == 297 and event.action == 1:  # GLFW F8
                raise Stopped("Stopped with F8.")
        if time.monotonic() >= self.deadline:
            raise Stopped("Time limit reached.")
        if m.screen_name() is not None:
            raise Stopped("A menu was opened.")
        info = m.world_info()
        if (info.name, info.address, info.dimension) != self.world:
            raise Stopped("World or dimension changed.")
        health = m.player_health()
        if health < self.health or health <= 6:
            raise Stopped("Damage detected or health too low.")
        self.health = health

    def wait(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.check()
            time.sleep(min(0.05, max(0, end - time.monotonic())))

    def use(self):
        self.check()
        try:
            m.player_press_use(True)
            self.wait(0.1)
        finally:
            m.player_press_use(False)

    def __exit__(self, exc_type, exc_value, traceback):
        # Attempt every cleanup even if the game disconnected during one call.
        for cleanup in (
            lambda: m.player_press_attack(False),
            lambda: m.player_press_use(False),
            lambda: m.player_press_forward(False),
            self.events.unregister_all,
        ):
            try:
                cleanup()
            except Exception as error:
                logging.getLogger(__name__).warning(
                    "Could not release a game input or listener: %s", error
                )


def nearby_blocks(predicate, reach=4.5):
    px, py, pz = m.player_position()
    eye = (px, py + 1.62, pz)
    positions = [
        (x, y, z)
        for x in range(math.floor(px - reach), math.floor(px + reach) + 1)
        for y in range(math.floor(eye[1] - reach), math.floor(eye[1] + reach) + 1)
        for z in range(math.floor(pz - reach), math.floor(pz + reach) + 1)
        if math.dist(eye, (x + 0.5, y + 0.5, z + 0.5)) <= reach
    ]
    states = m.getblocklist([list(pos) for pos in positions])
    matches = [
        (pos, state) for pos, state in zip(positions, states, strict=True) if predicate(state)
    ]
    return sorted(matches, key=lambda entry: math.dist(eye, entry[0]))


def aim_block(session, pos, offset=0.5):
    session.check()
    m.player_look_at(pos[0] + 0.5, pos[1] + offset, pos[2] + 0.5)
    session.wait(0.1)
    target = m.player_get_targeted_block(4.5)
    return target is not None and tuple(target.position) == tuple(pos)


def break_block(session, pos, expected, timeout=8):
    """Mine only the verified block; release attack before it can hit another."""
    if not aim_block(session, pos) or m.getblock(*pos) != expected:
        return False
    started = time.monotonic()
    try:
        while time.monotonic() - started < timeout:
            session.check()
            if m.getblock(*pos) != expected:
                return True
            target = m.player_get_targeted_block(4.5)
            if target is None or tuple(target.position) != tuple(pos):
                return False
            if m.player_get_targeted_entity(4.5) is not None:
                return False
            m.player_press_attack(True)
            session.wait(0.05)
        return False
    finally:
        m.player_press_attack(False)


def run(main, args):
    try:
        main(args)
    except (Stopped, ValueError) as error:
        m.echo(str(error))
