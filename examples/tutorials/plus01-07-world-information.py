# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/plus01.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 141.
# Original license: LICENSE in this directory.
import minescript as m
from minescript_plus import World
import time

raining = World.is_raining()
thundering = World.is_thundering()
hardcore = World.is_hardcore()
difficulty = World.get_difficulty()
spawn_pos = World.get_spawn_pos()
game_time = World.get_game_time()
day_time = World.get_day_time()

m.echo(f"Raining? {raining}")
m.echo(f"Thundering? {thundering}")
m.echo(f"Hardcore World? {hardcore}")
m.echo(f"Difficulty: {difficulty}")
m.echo(f"Spawn Position: {spawn_pos}")
m.echo(f"Game Time (ticks): {game_time}")
m.echo(f"Day Time (ticks): {day_time}")
time.sleep(2)
