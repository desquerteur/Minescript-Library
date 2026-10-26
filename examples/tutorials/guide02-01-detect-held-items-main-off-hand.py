# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 40.
# Original license: LICENSE in this directory.
import minescript as m

hands = m.player_hand_items()

# Main hand
if hands.main_hand:
    main_item = hands.main_hand.get('item', 'minecraft:air') if isinstance(hands.main_hand, dict) else str(hands.main_hand)
    if main_item != "minecraft:air":
        m.echo(f"Item in main hand: {main_item}")
    else:
        m.echo("Main hand is empty")
else:
    m.echo("Main hand is empty")

# Off hand
if hands.off_hand:
    off_item = hands.off_hand.get('item', 'minecraft:air') if isinstance(hands.off_hand, dict) else str(hands.off_hand)
    if off_item != "minecraft:air":
        m.echo(f"Item in off hand: {off_item}")
    else:
        m.echo("Off hand is empty")
else:
    m.echo("Off hand is empty")
