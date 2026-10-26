# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/plus01.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 114.
# Original license: LICENSE in this directory.
import minescript as m
from minescript_plus import Player
import time

latency = Player.get_latency()
game_mode = Player.get_game_mode()
is_creative = Player.is_creative()
is_survival = Player.is_survival()
skin_url = Player.get_skin_url()
food_level = Player.get_food_level()
saturation_level = Player.get_saturation_level()

m.echo(f"Latency: {latency} ms")
m.echo(f"Game Mode: {game_mode}")
m.echo(f"In Creative Mode? {is_creative}")
m.echo(f"In Survival Mode? {is_survival}")
m.echo(f"Skin URL: {skin_url}")
m.echo(f"Food Level: {food_level}")
m.echo(f"Saturation Level: {saturation_level}")
time.sleep(2)
