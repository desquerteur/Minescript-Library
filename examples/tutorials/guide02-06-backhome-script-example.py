# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 201.
# Original license: LICENSE in this directory.
import minescript as m
from minescript import EventQueue, EventType
import math

# Give the player a clock for testing
m.execute("give @p minecraft:clock 1")

# Record current player position (block coordinates)
x, y, z = m.player_position()
x, y, z = math.floor(x), math.floor(y), math.floor(z)
m.execute(f"setblock {x} {y-1} {z} gold_block")

def backhome():
    m.echo("Hold a clock and release Left Shift to teleport home!")

    with EventQueue() as eq:
        eq.register_key_listener()

        while True:
            event = eq.get()

            # Get hand items safely
            hands = m.player_hand_items()
            main_hand_item = None
            if hands and hands.main_hand:
                if isinstance(hands.main_hand, dict):
                    main_hand_item = hands.main_hand.get("item", None)
                else:
                    main_hand_item = str(hands.main_hand)

            # Check: main hand holds a clock + Left Shift released (action == 0)
            # if main_hand_item == "minecraft:clock":
            if  "minecraft:clock" in main_hand_item:
                if event.type == EventType.KEY and event.key == 340 and event.action == 0:
                    m.execute(f"tp @p {x} {y} {z}")
                    m.echo("Teleported home because holding a clock + left shift released")

if __name__ == "__main__":
    backhome()
