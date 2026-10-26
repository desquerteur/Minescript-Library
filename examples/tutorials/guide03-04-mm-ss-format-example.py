# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide03.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 118.
# Original license: LICENSE in this directory.
import minescript as m
import time

m.echo("Countdown start")

total_seconds = 10
objective_name = "timer"
display_title = "Countdown"
dummy_line = "Time"  # Dummy line for updating

# Create scoreboard with title "Countdown"
m.execute(f'scoreboard objectives add {objective_name} dummy "{display_title}"')

# Display on sidebar
m.execute(f'scoreboard objectives setdisplay sidebar {objective_name}')

prev_time_str = None

# Countdown loop
for t in range(total_seconds, 0, -1):
    minutes = t // 60
    seconds = t % 60
    time_str = f"{minutes:02d}:{seconds:02d}"  # 00:10, 00:09 ...

    # Set the current time line
    m.execute(f'scoreboard players set "{time_str}" {objective_name} 15')

    # Remove the previous line so only one line is visible
    if prev_time_str:
        m.execute(f'scoreboard players reset "{prev_time_str}" {objective_name}')

    prev_time_str = time_str
    time.sleep(1)

# Remove scoreboard after countdown
m.execute(f'scoreboard objectives setdisplay sidebar')
m.execute(f'scoreboard objectives remove {objective_name}')

m.echo("Countdown stop")
