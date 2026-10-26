# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic01.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 47.
# Original license: LICENSE in this directory.
import minescript
from math import floor

# Get the current player position (floats)
x, y, z = minescript.player_position()

# Convert to integers for clean display
# x, y, z = int(x), int(y), int(z)
x, y, z = floor(x), floor(y), floor(z)

# Show the position in chat
minescript.echo(f"Current Position: X={x}, Y={y}, Z={z}")
