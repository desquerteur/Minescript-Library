# SPDX-License-Identifier: MIT
"""Find a carried item and select it in the hotbar: \\equip ITEM_ID."""

import sys

import minescript as m

from automation_common import Stopped, run


def main(args):
    if len(args) != 1:
        raise ValueError("Usage: \\equip ITEM_ID; example: \\equip iron_pickaxe")
    wanted = args[0] if ":" in args[0] else "minecraft:" + args[0]
    items = [
        item
        for item in m.player_inventory()
        if item.item == wanted and item.count > 0 and item.slot is not None and 0 <= item.slot <= 35
    ]
    if not items:
        raise Stopped(f"No {wanted} in your main inventory or hotbar.")
    item = min(items, key=lambda stack: stack.slot)
    slot = item.slot if item.slot <= 8 else m.player_inventory_slot_to_hotbar(item.slot)
    m.player_inventory_select_slot(slot)
    m.echo(f"Selected {wanted} in hotbar slot {slot + 1}.")


if __name__ == "__main__":
    run(main, sys.argv[1:])
