# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/basic02.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 171.
# Original license: LICENSE in this directory.
import minescript as m
import time

with m.EventQueue() as events:
    events.register_chat_listener()
    m.echo("Type 's a m p l e' in chat to jump! Please remove the spaces.")

    while True:
        event = events.get()
        if event.type == m.EventType.CHAT and "sample" in event.message.lower():
            m.echo("Jumping!")
            m.player_press_jump(True)
            time.sleep(0.3)
            m.player_press_jump(False)

# Using "jump" would cause continuous jumping,
# so I use "sample" instead. 
# There are ways to avoid this, but they make the code longer,
# so I keep it simple here. 
# Considering future tutorials to improve this code step-by-step.

