# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide03.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 87.
# Original license: LICENSE in this directory.
import minescript as m
import time

m.echo("Countdown start")

num = 10

# Create a scoreboard with display name "Timer" (shown at top of sidebar)
m.execute('scoreboard objectives add timer dummy "Timer"')

# Use a dummy player name for display numbers, e.g., "Countdown"
m.execute(f'scoreboard players set Countdown timer {num}')

# Display the scoreboard on the sidebar
m.execute('scoreboard objectives setdisplay sidebar timer')

# Countdown loop
for t in range(num, 0, -1):
    m.execute(f'scoreboard players set Countdown timer {t}')
    time.sleep(1)

# Hide and remove the scoreboard
m.execute('scoreboard objectives setdisplay sidebar')  # Clear display
m.execute('scoreboard objectives remove timer')

m.echo("Countdown stop")
