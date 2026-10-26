# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide03.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 177.
# Original license: LICENSE in this directory.
import minescript as m
import time

m.echo("Countdown start")

num = 10

# Create a bossbar
m.execute('bossbar add timer "Countdown"')
m.execute('bossbar set timer color blue')
m.execute(f'bossbar set timer max {num}')   # Maximum value (seconds)
m.execute(f'bossbar set timer value {num}') # Current value
m.execute('bossbar set timer players @a')  # Display to all players

# Countdown loop
for t in range(num, 0, -1):
    # Update value
    m.execute(f'bossbar set timer value {t}')
    
    # Update title to include countdown number
    m.execute(f'bossbar set timer name "Countdown {t}"')
    
    time.sleep(1)

# Remove bossbar
m.execute('bossbar remove timer')
m.echo("Countdown stop")
