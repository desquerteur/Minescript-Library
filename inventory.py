# SPDX-License-Identifier: MIT
# Adapted from LaosyAlex/Scripts-For-MCSMP/logPlayerInventory.py.
# Copyright (c) 2026 Alex Phommarath. See licenses/Scripts-For-MCSMP-MIT.txt.
"""Count your inventory supplies: \\inventory [ITEM_FILTER]."""

import sys
from collections import Counter

import minescript as m

from automation_common import run


def main(args):
    if len(args) > 1:
        raise ValueError("Usage: \\inventory [ITEM_FILTER]")
    query = args[0].casefold() if args else ""
    items = [
        item
        for item in m.player_inventory()
        if item.slot is not None
        and 0 <= item.slot <= 35
        and item.count > 0
        and item.item != "minecraft:air"
    ]
    totals = Counter()
    for item in items:
        if query in item.item.casefold():
            totals[item.item] += item.count
    for item_id, count in sorted(totals.items()):
        m.echo(f"{item_id}: {count}")
    if not totals:
        m.echo("No matching items in your main inventory or hotbar.")
    used = len({item.slot for item in items})
    m.echo(f"Main inventory and hotbar: {used}/36 slots used, {36 - used} free.")


if __name__ == "__main__":
    run(main, sys.argv[1:])
