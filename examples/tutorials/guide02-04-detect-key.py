# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 140.
# Original license: LICENSE in this directory.
import minescript as m
from minescript import EventQueue, EventType

with EventQueue() as eq:
    eq.register_key_listener()
    
    while True:
        event = eq.get()
        
        # Left Shift Key
        if event.type == EventType.KEY and event.key == 340 and event.action == 1:
            m.echo("Left shift key pressed")
        elif event.type == EventType.KEY and event.key == 340 and event.action == 0:
            m.echo("Left shift key released")
        
        # F12 Key
        elif event.type == EventType.KEY and event.key == 301 and event.action == 1:
            m.echo("F12 key pressed")
        elif event.type == EventType.KEY and event.key == 301 and event.action == 0:
            m.echo("F12 key released")
