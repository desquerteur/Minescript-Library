"""Helpers for Minecraft block identifiers and block states."""

from __future__ import annotations

from ..generated.block_catalog import Blocks


def _stringify_state_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def split_block_state(block_id: str) -> tuple[str, dict[str, str]]:
    """Split a block id like ``minecraft:oak_log[axis=y]`` into base and states."""
    if "[" not in block_id:
        return block_id, {}

    base, raw_states = block_id.rstrip("]").split("[", 1)
    states = {}
    for chunk in raw_states.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        key, value = chunk.split("=", 1)
        states[key.strip()] = value.strip()
    return base, states


def block_name(block_id: str, keep_namespace: bool = False) -> str:
    """Return the base block name, optionally keeping the namespace prefix."""
    base, _ = split_block_state(block_id)
    if keep_namespace or ":" not in base:
        return base
    return base.split(":", 1)[1]


def with_block_states(base_block: str, **states) -> str:
    """Append block state pairs to a base block id."""
    if not states:
        return base_block
    rendered_states = ",".join(
        f"{name}={_stringify_state_value(value)}" for name, value in states.items()
    )
    return f"{base_block}[{rendered_states}]"


def is_unloaded_block(block_id: str | None) -> bool:
    """Return ``True`` when a block id is missing or resolves to ``minecraft:void_air``."""
    return not block_id or block_id == Blocks.VOID_AIR
