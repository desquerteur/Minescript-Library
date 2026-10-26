# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide05.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 139.
# Original license: LICENSE in this directory.
import minescript as m
import threading
import time
from minescript import EventQueue, EventType

# ----------------------
# Timer state
# ----------------------
timer_length = 30
timer_value = timer_length
timer_running = False
timer_thread = None  # Countdown thread

# ----------------------
# Bossbar / timer functions
# ----------------------
def create_bossbar():
    m.execute('bossbar add timer "Countdown"')
    m.execute('bossbar set timer color blue')
    m.execute(f'bossbar set timer max {timer_length}')
    m.execute(f'bossbar set timer value {timer_value}')
    m.execute('bossbar set timer players @a')

def remove_bossbar():
    m.execute('bossbar remove timer')

def update_bossbar():
    minutes = timer_value // 60
    seconds = timer_value % 60
    time_text = f"{minutes:02d}:{seconds:02d}"
    m.execute(f'bossbar set timer name "{time_text}"')
    m.execute(f'bossbar set timer value {timer_value}')

def countdown():
    global timer_value, timer_running
    while timer_running and timer_value > 0:
        update_bossbar()
        time.sleep(1)
        timer_value -= 1
    if timer_running:
        m.echo("⏰ Timer finished!")
        m.execute('title @a title {"text":"⏰ Time\'s up!","color":"red"}')
    remove_bossbar()
    timer_running = False

# ----------------------
# Chat commands
# ----------------------
def show_help():
    m.echo("""
Timer Commands:
--settime <seconds> : Set countdown time
--start             : Start countdown
--stop              : Stop countdown
--help              : Show this message
""")

# ----------------------
# Main loop
# ----------------------
def main():
    global timer_length, timer_value, timer_running, timer_thread

    eq = EventQueue()
    eq.register_chat_listener()
    m.echo("Countdown timer ready! Type --help for commands.")

    while True:
        event = eq.get()
        if not event or event.type != EventType.CHAT:
            continue

        msg = event.message.strip()

        # Remove <Player> prefix
        if msg.startswith("<") and ">" in msg:
            msg = msg.split(">", 1)[1].strip()

        if not msg.startswith("--"):
            continue

        if msg.startswith("--settime"):
            try:
                seconds = int(msg.split()[1])
                timer_length = max(1, seconds)
                timer_value = timer_length
                m.echo(f"Timer set to {timer_length} seconds.")
            except:
                m.echo("Invalid usage. Example: --settime 60")

        elif msg == "--start":
            if timer_running:
                m.echo("Timer is already running.")
            else:
                timer_running = True
                timer_value = timer_length
                create_bossbar()
                timer_thread = threading.Thread(target=countdown, daemon=True)
                timer_thread.start()
                m.echo("▶️ Timer started!")

        elif msg == "--stop":
            if timer_running:
                timer_running = False
                m.echo("⏹ Timer stopped manually.")
            remove_bossbar()

        elif msg == "--help":
            show_help()

if __name__ == "__main__":
    main()
