# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide05.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 34.
# Original license: LICENSE in this directory.
import minescript as m
from minescript import EventQueue, EventType

eq = EventQueue()
eq.register_chat_listener()
m.echo("Chat listener ready!")

while True:
    event = eq.get()
    if not event or event.type != EventType.CHAT:
        continue

    msg = event.message
    # Remove player name prefix
    if msg.startswith("<") and ">" in msg:
        msg = msg.split(">", 1)[1].strip()

    # Skip if condition not met
    if not msg.startswith("--"):
        continue

    # Process only messages starting with --
    m.echo(f"Processing command-style chat: {msg}")
