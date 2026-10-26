# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide05.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 66.
# Original license: LICENSE in this directory.
import minescript as m
from minescript import EventQueue, EventType

def main():
    eq = EventQueue()
    eq.register_chat_listener()

    m.echo("Chat command demo ready! Type --help for commands.")

    while True:
        event = eq.get()
        if not event or event.type != EventType.CHAT:
            continue

        msg = event.message.strip()

        if msg.startswith("<") and ">" in msg:
            msg = msg.split(">", 1)[1].strip()

        # Remove <Player> prefix
        if not msg.startswith("--"):
            continue

        if msg == "--help":
            m.echo("""
Available commands (type in chat):
--noon       : Set time to noon
--pinksheep  : Summon a pink sheep
--cheat      : Give OP items
""")

        elif msg == "--noon":
            m.execute("time set noon")
            m.echo("☀️ Time set to noon!")

        elif msg == "--pinksheep":
            m.execute("summon minecraft:sheep ^3 ^ ^ {Color:6}")
            m.echo("🐑 A pink sheep appeared!")

        elif msg == "--cheat":
            items = [
                "minecraft:netherite_sword",
                "minecraft:netherite_helmet",
                "minecraft:netherite_chestplate",
                "minecraft:netherite_leggings",
                "minecraft:netherite_boots",
                "minecraft:enchanted_golden_apple"
            ]
            for item in items:
                m.execute(f"give @p {item} 1")
            m.echo("🎁 OP items granted!")

if __name__ == "__main__":
    main()
