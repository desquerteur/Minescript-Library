# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 63.
# Original license: LICENSE in this directory.
import minescript as m

# Face forward
# m.player_set_orientation(0, 0)

# Get the targeted block
block = m.player_get_targeted_block(10)
if block:
    m.echo(f"Target Block: {block.type} @ {block.position}")
else:
    m.echo("No block in crosshairs")
