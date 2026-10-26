# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 229.
# Original license: LICENSE in this directory.
import minescript as m
import time

m.execute('/item replace entity @p hotbar.0 with minecraft:fishing_rod')
map_enchants = [
    "minecraft:luck_of_the_sea 3",
    "minecraft:lure 3",
    "minecraft:unbreaking 3",
    "minecraft:mending 1"
]
for ench in map_enchants:
    m.execute(f"/enchant @p {ench}")

def find_bobber():
    for entity in m.entities():
        if "fishing_bobber" in entity.type.lower():
            return entity
    return None

def wait_for_bite(bobber, timeout=30):
    start = time.time()
    last_y = bobber.position[1]
    while time.time() - start < timeout:
        entity = find_bobber()
        if entity:
            y = entity.position[1]
            if y - last_y > 0.2:
                return True
            last_y = y
        time.sleep(0.1)
    return False

while True:
    m.player_press_use(True)
    m.player_press_use(False)
    time.sleep(2)

    bobber = find_bobber()
    if bobber and wait_for_bite(bobber):
        m.echo("Fish caught!")
        m.player_press_use(True)
        m.player_press_use(False)

    time.sleep(1)

# This will keep fishing forever, so please stop it with "\killjob -1".
# There are ways to avoid this, but they make the code longer,
# so I keep it simple here. 
# Considering future tutorials to improve this code step-by-step.

