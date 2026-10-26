# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 131.
# Original license: LICENSE in this directory.
import minescript as m

# Check items in both hands
hands = m.player_hand_items()
m.echo(f"Main hand: {hands.main_hand.item}")
m.echo(f"Off hand: {hands.off_hand.item}")

# Show inventory items
for item in m.player_inventory():
    m.echo(f"Slot {item.slot}: {item.item} x{item.count}")
