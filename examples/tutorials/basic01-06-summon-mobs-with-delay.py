# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic01.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 140.
# Original license: LICENSE in this directory.
from time import sleep
from minescript import player_position, echo, execute
from math import floor

# Get and convert player position
# x, y, z = map(int, player_position())
x, y, z = map(floor, player_position())

# Summon an Allay at x+3, z+3
execute(f"/summon minecraft:allay {x+3} {y} {z+3} {{}}")
sleep(3)

# Summon a warm-variant cow (note: "variant" NBT works only in some versions/mods)
execute(f'/summon minecraft:cow {x+3} {y} {z+3} {{"variant":"warm"}}')
sleep(3)

# Summon a cold-variant chicken (same note as above)
execute(f'/summon minecraft:chicken {x+3} {y} {z+3} {{"variant":"cold"}}')
