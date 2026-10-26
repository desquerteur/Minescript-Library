# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 244.
# Original license: LICENSE in this directory.
import minescript as m
from minescript import EventQueue, EventType
import math
import time

# Give the player a clock for testing
m.execute("give @p minecraft:clock 1")

# Record current player position (block coordinates)
x, y, z = m.player_position()
x, y, z = math.floor(x), math.floor(y), math.floor(z)
m.execute(f"setblock {x} {y-1} {z} gold_block")

def backhome():
    m.echo("Hold a clock and release Left Shift to teleport home!")

    # Use legacy dict return to reliably read hand items
    m.options.legacy_dict_return_values = True

    with EventQueue() as eq:
        eq.register_key_listener()

        prev_event_hand = None

        while True:
            event = eq.get()

            # Get hand items
            hands = m.player_hand_items()
            main_hand_item = hands.get("main_hand", {}).get("item", "")

            # Check: main hand holds a clock + Left Shift released (key 340)
            if main_hand_item == "minecraft:clock":
                if event.type == EventType.KEY and event.key == 340 and event.action == 0:
                    m.execute(f"tp @p {x} {y} {z}")
                    m.echo("Teleported home because holding a clock + left shift released")

if __name__ == "__main__":
    backhome()
