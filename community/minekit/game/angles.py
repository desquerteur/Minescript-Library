"""Angle helpers for player orientation."""

from __future__ import annotations

import math

from ..internal.enums import Direction
from ..internal.types import BlockPos, Vec3, YawPitch

YAW_SOUTH = 0.0
YAW_WEST = 90.0
YAW_NORTH = 180.0
YAW_EAST = -90.0

PITCH_LEVEL = 0.0
PITCH_BLOCK_FACE = 80.0
PITCH_DOWN = 90.0

_DIRECTION_TO_YAW = {
    Direction.NORTH: YAW_NORTH,
    Direction.SOUTH: YAW_SOUTH,
    Direction.EAST: YAW_EAST,
    Direction.WEST: YAW_WEST,
}


def yaw_for(direction: Direction) -> float:
    """Return the canonical yaw angle for a cardinal ``Direction``."""
    return _DIRECTION_TO_YAW[Direction(direction)]


def normalize_yaw(angle: float) -> float:
    """Wrap a yaw angle into Minecraft's ``[-180, 180]`` range."""
    normalized = (float(angle) + 180.0) % 360.0 - 180.0
    if normalized == -180.0 and angle > 0:
        return 180.0
    return normalized


def clamp_pitch(angle: float) -> float:
    """Clamp a pitch angle into Minecraft's valid ``[-90, 90]`` range."""
    return max(-90.0, min(90.0, float(angle)))


def yaw_pitch_to_block(from_pos: Vec3, block_pos: BlockPos) -> YawPitch:
    """Return the yaw and pitch needed to look at the center of a block."""
    target_x = float(block_pos[0]) + 0.5
    target_y = float(block_pos[1]) + 0.5
    target_z = float(block_pos[2]) + 0.5

    dx = target_x - float(from_pos[0])
    dy = target_y - float(from_pos[1])
    dz = target_z - float(from_pos[2])

    horizontal_distance = math.hypot(dx, dz)
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = math.degrees(-math.atan2(dy, horizontal_distance))
    return normalize_yaw(yaw), clamp_pitch(pitch)
