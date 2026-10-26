# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/plus01.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 74.
# Original license: LICENSE in this directory.
import minescript as m
from minescript_plus import Inventory
import time

# Try to open the chest in front and search for "minecraft:diamond"
slot = Inventory.find_item("minecraft:diamond", container=True, try_open=True)
if slot is not None:
    m.echo(f"✅ Found diamond in chest! Slot: {slot}")
else:
    m.echo("❌ No diamond found in chest.")
time.sleep(2)
