# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 105.
# Original license: LICENSE in this directory.
import minescript as m
from minescript import EventQueue, EventType

with EventQueue() as eq:
    eq.register_mouse_listener()
    
    while True:
        event = eq.get()
        
        if event.type == EventType.MOUSE:
            # Left Click Pressed
            if event.button == 0 and event.action == 1:
                m.echo("Left click pressed")
            # Right Click Pressed
            elif event.button == 1 and event.action == 1:
                m.echo("Right click pressed")
