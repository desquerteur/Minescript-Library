# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/guide/guide03.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 37.
# Original license: LICENSE in this directory.
import minescript as m
import time

m.echo("countdown start")

num = 10

# Countdown loop
for t in range(num, 0, -1):
    m.execute(f'title @a actionbar ["Countdown: {t}"]')
    time.sleep(1)

# Clear the actionbar message
m.execute('title @a actionbar [""]')
m.echo("countdown stop")
