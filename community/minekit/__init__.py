"""Vendorable DX layer for Minescript.

Copy the ``mc`` package into a Minescript project and import it directly:

    from mc.control.player import PlayerController

The package root stays lazy so that pure helper modules can be imported without
pulling in the Minescript runtime immediately.
"""

from importlib import import_module

__all__ = [
    "Action",
    "Blocks",
    "Direction",
    "Entities",
    "EntitySort",
    "HotbarSlot",
    "HotkeyController",
    "InventoryController",
    "Items",
    "KeyboardController",
    "LogController",
    "KeyBind",
    "KeyCode",
    "MouseButton",
    "MouseController",
    "PITCH_BLOCK_FACE",
    "PITCH_DOWN",
    "PITCH_LEVEL",
    "PlayerController",
    "TimingController",
    "SECONDS_PER_TICK",
    "TICKS_PER_SECOND",
    "current_game_tick",
    "YAW_EAST",
    "YAW_NORTH",
    "YAW_SOUTH",
    "YAW_WEST",
    "clamp_pitch",
    "seconds_to_ticks",
    "ticks_to_seconds",
    "wait_ticks",
    "normalize_yaw",
    "yaw_for",
    "yaw_pitch_to_block",
]

_EXPORTS = {
    "Action": ("mc.internal.enums", "Action"),
    "Blocks": ("mc.generated.block_catalog", "Blocks"),
    "Direction": ("mc.internal.enums", "Direction"),
    "Entities": ("mc.generated.entity_catalog", "Entities"),
    "EntitySort": ("mc.internal.enums", "EntitySort"),
    "HotbarSlot": ("mc.internal.enums", "HotbarSlot"),
    "HotkeyController": ("mc.control.hotkeys", "HotkeyController"),
    "InventoryController": ("mc.control.inventory", "InventoryController"),
    "Items": ("mc.generated.item_catalog", "Items"),
    "KeyboardController": ("mc.control.keyboard", "KeyboardController"),
    "LogController": ("mc.control.logs", "LogController"),
    "KeyBind": ("mc.internal.enums", "KeyBind"),
    "KeyCode": ("mc.internal.enums", "KeyCode"),
    "MouseButton": ("mc.internal.enums", "MouseButton"),
    "MouseController": ("mc.control.mouse", "MouseController"),
    "PITCH_BLOCK_FACE": ("mc.game.angles", "PITCH_BLOCK_FACE"),
    "PITCH_DOWN": ("mc.game.angles", "PITCH_DOWN"),
    "PITCH_LEVEL": ("mc.game.angles", "PITCH_LEVEL"),
    "PlayerController": ("mc.control.player", "PlayerController"),
    "TimingController": ("mc.control.timing", "TimingController"),
    "SECONDS_PER_TICK": ("mc.game.timing", "SECONDS_PER_TICK"),
    "TICKS_PER_SECOND": ("mc.game.timing", "TICKS_PER_SECOND"),
    "current_game_tick": ("mc.game.timing", "current_game_tick"),
    "YAW_EAST": ("mc.game.angles", "YAW_EAST"),
    "YAW_NORTH": ("mc.game.angles", "YAW_NORTH"),
    "YAW_SOUTH": ("mc.game.angles", "YAW_SOUTH"),
    "YAW_WEST": ("mc.game.angles", "YAW_WEST"),
    "clamp_pitch": ("mc.game.angles", "clamp_pitch"),
    "seconds_to_ticks": ("mc.game.timing", "seconds_to_ticks"),
    "ticks_to_seconds": ("mc.game.timing", "ticks_to_seconds"),
    "wait_ticks": ("mc.game.timing", "wait_ticks"),
    "normalize_yaw": ("mc.game.angles", "normalize_yaw"),
    "yaw_for": ("mc.game.angles", "yaw_for"),
    "yaw_pitch_to_block": ("mc.game.angles", "yaw_pitch_to_block"),
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    return getattr(module, attr_name)
