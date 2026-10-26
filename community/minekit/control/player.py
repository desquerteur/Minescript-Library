"""Player-focused high-level controller."""

from __future__ import annotations

import math
import time

import minescript

from ..game.angles import clamp_pitch, normalize_yaw, yaw_for, yaw_pitch_to_block
from ..internal.enums import Action, Direction
from .inventory import InventoryController

_ACTION_TO_FUNCTION = {
    Action.FORWARD: minescript.player_press_forward,
    Action.BACKWARD: minescript.player_press_backward,
    Action.LEFT: minescript.player_press_left,
    Action.RIGHT: minescript.player_press_right,
    Action.JUMP: minescript.player_press_jump,
    Action.SPRINT: minescript.player_press_sprint,
    Action.SNEAK: minescript.player_press_sneak,
    Action.PICK_ITEM: minescript.player_press_pick_item,
    Action.USE: minescript.player_press_use,
    Action.ATTACK: minescript.player_press_attack,
    Action.SWAP_HANDS: minescript.player_press_swap_hands,
    Action.DROP: minescript.player_press_drop,
}
_MOVEMENT_ACTIONS = {Action.FORWARD, Action.BACKWARD, Action.LEFT, Action.RIGHT}


class PlayerController:
    """High-level facade for player movement, look direction and player actions."""

    def __init__(self, *, sleep_fn=time.sleep, player_nbt: bool = True):
        """Create a player controller.

        Args:
            sleep_fn: Delay function used by helpers such as ``tap`` and ``look_at_block``.
            player_nbt: Whether player snapshots should include NBT by default.
        """
        self._sleep = sleep_fn
        self._player_nbt = bool(player_nbt)
        self.inventory = InventoryController()

    def snapshot(self, *, nbt: bool | None = None):
        """Return the current player snapshot reported by Minescript.

        Args:
            nbt: Override whether the snapshot should include NBT. Defaults to
                the controller-wide ``player_nbt`` setting.
        """
        if nbt is None:
            nbt = self._player_nbt
        return minescript.player(nbt=nbt)

    def position(self):
        """Return the player's current ``(x, y, z)`` position."""
        return tuple(minescript.player_position())

    def orientation(self):
        """Return the player's current ``(yaw, pitch)`` orientation."""
        return tuple(minescript.player_orientation())

    def look(self, yaw: float = None, pitch: float = None, direction: Direction = None):
        """Set the player's look direction.

        Args:
            yaw: Horizontal angle in Minecraft degrees.
            pitch: Vertical angle in Minecraft degrees.
            direction: Cardinal direction shortcut. When provided, it overrides ``yaw``.
        """
        current_yaw, current_pitch = self.orientation()
        if direction is not None:
            yaw = yaw_for(direction)
        if yaw is None:
            yaw = current_yaw
        if pitch is None:
            pitch = current_pitch
        return minescript.player_set_orientation(normalize_yaw(yaw), clamp_pitch(pitch))

    def look_at_block(self, block_pos, smooth: bool = False):
        """Aim the camera at the center of a block position.

        Args:
            block_pos: Target block as ``(x, y, z)``.
            smooth: Interpolate the movement instead of snapping instantly.
        """
        target_yaw, target_pitch = yaw_pitch_to_block(self.position(), block_pos)
        if not smooth:
            return self.look(yaw=target_yaw, pitch=target_pitch)

        current_yaw, current_pitch = self.orientation()
        yaw_delta = normalize_yaw(target_yaw - current_yaw)
        pitch_delta = target_pitch - current_pitch
        steps = 12
        delay = 0.01

        for step in range(1, steps + 1):
            factor = step / steps
            next_yaw = normalize_yaw(current_yaw + yaw_delta * factor)
            next_pitch = clamp_pitch(current_pitch + pitch_delta * factor)
            minescript.player_set_orientation(next_yaw, next_pitch)
            self._sleep(delay)
        return True

    def tap(self, action: Action, duration: float = 0.05):
        """Press a player action for a short amount of time.

        Args:
            action: Action to trigger, such as ``Action.ATTACK`` or ``Action.USE``.
            duration: How long to hold the action before releasing it.
        """
        press = _ACTION_TO_FUNCTION[Action(action)]
        press(True)
        self._sleep(duration)
        press(False)

    def spam_key(
        self,
        action: Action,
        count: int,
        press_time: float = 0.05,
        interval: float = 0.03,
    ):
        """Repeat a player action multiple times.

        Args:
            action: Action to repeat.
            count: Number of press-release cycles to execute.
            press_time: How long each press stays held down.
            interval: Delay between presses.
        """
        if count < 0:
            raise ValueError("count must be >= 0")
        for index in range(count):
            self.tap(action, duration=press_time)
            if index + 1 < count and interval > 0:
                self._sleep(interval)

    def step(self, direction, duration: float = 0.03):
        """Take a short movement step.

        Args:
            direction: Either a cardinal ``Direction`` or a movement ``Action``.
            duration: How long the movement key stays pressed.
        """
        if isinstance(direction, Direction):
            _, current_pitch = self.orientation()
            self.look(direction=direction, pitch=current_pitch)
            self.tap(Action.FORWARD, duration=duration)
            return

        action = Action(direction)
        if action not in _MOVEMENT_ACTIONS:
            raise ValueError(f"step expects a movement action, got {action.value!r}")
        self.tap(action, duration=duration)

    def center_on_block(self, tolerance: float = 0.05, step_duration: float = 0.03):
        """Nudge the player toward the center of the current block.

        Args:
            tolerance: Maximum accepted offset from the block center on X and Z.
            step_duration: Duration used by each corrective movement tap.
        """
        while True:
            x, _, z = self.position()
            center_x = math.floor(x) + 0.5
            center_z = math.floor(z) + 0.5

            if abs(x - center_x) > tolerance:
                self.step(Action.RIGHT if x < center_x else Action.LEFT, duration=step_duration)
                continue

            if abs(z - center_z) > tolerance:
                self.step(
                    Action.FORWARD if z < center_z else Action.BACKWARD,
                    duration=step_duration,
                )
                continue

            break
