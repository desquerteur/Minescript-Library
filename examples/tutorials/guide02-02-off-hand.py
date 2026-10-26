# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 67.
# Original license: LICENSE in this directory.
import minescript as m

# Use legacy dict format
m.options.legacy_dict_return_values = True
hands = m.player_hand_items()

# Main hand
if hands.get("main_hand"):
    m.echo(f"Item in main hand: {hands['main_hand']['item']}")
else:
    m.echo("Main hand is empty")

# Off hand
if hands.get("off_hand"):
    m.echo(f"Item in off hand: {hands['off_hand']['item']}")
else:
    m.echo("Off hand is empty")
