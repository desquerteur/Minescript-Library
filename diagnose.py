# SPDX-License-Identifier: MIT
# Adapted from Minescripters/Diag/diag.pyj.
# Copyright (c) 2026 RazrCraft. See licenses/Diag-MIT.txt.
"""Show Minecraft, Minescript, and Python versions: \\diagnose."""

import sys

import minescript as m

from automation_common import run


def main(args):
    if args:
        raise ValueError("Usage: \\diagnose")
    info = m.version_info()
    m.echo("Minescript Library diagnostics (adapted from RazrCraft's Diag)")
    for label, field in (
        ("Minecraft", "minecraft"),
        ("Minescript", "minescript"),
        ("Mod loader", "mod_loader"),
        ("Operating system", "os_name"),
    ):
        m.echo(f"{label}: {getattr(info, field, 'unavailable')}")
    m.echo(f"Python: {sys.version.split()[0]}")
    m.echo("Shared library import: OK")


if __name__ == "__main__":
    run(main, sys.argv[1:])
