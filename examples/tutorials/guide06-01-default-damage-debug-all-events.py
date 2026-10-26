# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide06.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 27.
# Original license: LICENSE in this directory.
import minescript as m
from minescript import EventQueue, EventType

eq = EventQueue()
eq.register_damage_listener()

m.echo("⚡ Default DamageEvent debug mode: waiting for damage...")

while True:
    event = eq.get()
    if not event or event.type != EventType.DAMAGE:
        continue

    # Inspect all DAMAGE events
    m.echo(f"--- DAMAGE EVENT ---")
    m.echo(f"entity_uuid = {event.entity_uuid}")
    m.echo(f"cause_uuid  = {event.cause_uuid}")
    m.echo(f"source      = {event.source}")
    m.echo(f"full event  = {event.__dict__}")
