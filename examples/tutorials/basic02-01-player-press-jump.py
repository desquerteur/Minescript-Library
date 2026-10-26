# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 35.
# Original license: LICENSE in this directory.
import minescript as m
import time

# Move forward briefly
m.player_press_forward(True)
time.sleep(0.5)
m.player_press_forward(False)

# Jump
m.player_press_jump(True)
time.sleep(0.2)
m.player_press_jump(False)
