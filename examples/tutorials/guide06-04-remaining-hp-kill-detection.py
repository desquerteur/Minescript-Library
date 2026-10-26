# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide06.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 129.
# Original license: LICENSE in this directory.
import minescript as m
from minescript import EventQueue, EventType, player, entities

local_player = player()
local_uuid = local_player.uuid
m.echo(f"⚔️ Damage listener active for {local_player.name} (HP & kill tracking)")

eq = EventQueue()
eq.register_damage_listener()

while True:
    event = eq.get()
    if not event or event.type != EventType.DAMAGE:
        continue

    if event.source not in ["player", "arrow", "trident"]:
        continue

    if event.cause_uuid != local_uuid:
        continue

    mobs = entities(uuid=event.entity_uuid)
    if not mobs:
        continue

    mob = mobs[0]
    hp = getattr(mob, "health", None)

    if hp is not None:
        if hp > 0:
            m.echo(f"⚔️ You hit {mob.type} (HP left: {hp})")
        else:
            m.echo(f"💀 You killed {mob.type}!")
    else:
        m.echo(f"⚔️ You hit {mob.type}")
