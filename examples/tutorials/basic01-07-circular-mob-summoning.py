# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic01.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 167.
# Original license: LICENSE in this directory.
from time import sleep
import math
from minescript import player_position, echo, execute

# x, y, z = map(int, player_position())
x, y, z = map(math.floor, player_position())

mob = "allay"
num_mobs = 12
radius = 1

for i in range(num_mobs):
    angle = 2 * math.pi * i / num_mobs
    dx = round(math.cos(angle) * radius, 2)
    dz = round(math.sin(angle) * radius, 2)
    sx = x + dx
    sy = y
    sz = z + dz
    execute(f'/summon minecraft:{mob} {sx} {sy} {sz} {{}}')
