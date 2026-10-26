# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/plus01.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 57.
# Original license: LICENSE in this directory.
import minescript as m
from minescript_plus import Inventory
import time

slot = Inventory.find_item("minecraft:diamond")
if slot is not None:
    m.echo(f"✅ Diamond found in inventory! Slot: {slot}")
else:
    m.echo("❌ No diamond found in inventory.")
time.sleep(2)
