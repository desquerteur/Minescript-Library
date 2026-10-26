# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 201.
# Original license: LICENSE in this directory.
import minescript as m
import time

m.execute('/give @p minecraft:sweet_berries 64')

m.echo("Auto walking started")

while True:
    m.player_press_forward(True)
    m.player_press_use(True)
    time.sleep(0.2)
    m.player_press_use(False)
    time.sleep(1)

# This will keep walking forever, so please stop it with "\killjob -1".
# There are ways to avoid this, but they make the code longer,
# so I keep it simple here. 
# Considering future tutorials to improve this code step-by-step.

