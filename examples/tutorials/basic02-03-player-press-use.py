# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 95.
# Original license: LICENSE in this directory.
import minescript as m
import time

# Give oak sapling to main hand
m.execute("/item replace entity @p hotbar.0 with minecraft:oak_sapling")

# Get current player position
x, y, z = m.player_position()
# Look at the ground 3 blocks ahead
m.player_look_at(x, y - 1, z + 3)

# Right-click to use (try to plant the sapling)
m.player_press_use(True)
time.sleep(0.2)
m.player_press_use(False)
