"""Thin builders around command strings executed through Minescript."""

from __future__ import annotations

import json

import minescript

from ..internal.types import BlockPos
from .blocks import with_block_states


def _format_pos(pos: BlockPos) -> str:
    return f"{int(pos[0])} {int(pos[1])} {int(pos[2])}"


def _quote_snbt_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return "'" + escaped + "'"


def _to_snbt(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return _quote_snbt_string(value)
    if isinstance(value, list):
        return "[" + ",".join(_to_snbt(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            parts.append(f"{key}:{_to_snbt(item)}")
        return "{" + ",".join(parts) + "}"
    raise TypeError(f"Unsupported SNBT value: {value!r}")


def run(command: str):
    """Execute a raw command string through Minescript."""
    return minescript.execute(command)


def set_block(pos: BlockPos, block: str, **states):
    """Build and run a ``/setblock`` command."""
    block_id = with_block_states(block, **states)
    return run(f"/setblock {_format_pos(pos)} {block_id}")


def fill(pos1: BlockPos, pos2: BlockPos, block: str, **states):
    """Build and run a ``/fill`` command."""
    block_id = with_block_states(block, **states)
    return run(f"/fill {_format_pos(pos1)} {_format_pos(pos2)} {block_id}")


def merge_block_data(pos: BlockPos, data):
    """Build and run ``/data merge block`` using a dict or raw SNBT string."""
    payload = data if isinstance(data, str) else _to_snbt(data)
    return run(f"/data merge block {_format_pos(pos)} {payload}")


def sign_nbt(lines) -> str:
    """Build SNBT for sign text from up to four lines."""
    rendered = {}
    normalized_lines = list(lines)[:4]
    while len(normalized_lines) < 4:
        normalized_lines.append("")

    for index, line in enumerate(normalized_lines, start=1):
        component = json.dumps({"text": str(line)}, separators=(",", ":"))
        rendered[f"Text{index}"] = component
    return _to_snbt(rendered)
