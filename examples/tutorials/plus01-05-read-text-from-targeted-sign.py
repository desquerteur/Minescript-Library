# SPDX-License-Identifier: MIT
# Extracted from sam-ple/minescript-sample/docs/tutorials/plus01.md at f1ff8518c907ffc91144184768e0b8f3563f585c, line 92.
# Original license: LICENSE in this directory.
import minescript as m
from minescript_plus import World
import time

sign_text = World.get_targeted_sign_text()
if sign_text:
    m.echo("Sign front lines:")
    for line in sign_text[:4]:
        m.echo(line)
    m.echo("Sign back lines:")
    for line in sign_text[4:]:
        m.echo(line)
else:
    m.echo("No sign targeted.")
time.sleep(2)
