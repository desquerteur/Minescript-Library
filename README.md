# Minescript-Library

Four MIT-licensed mining and farming commands for Minescript 5.0 and Python
3.10 or later. Two community scripts were adapted, and two small helpers were
added for this collection. Sources, original snapshots, and full upstream
licenses are recorded in [SOURCES.md](SOURCES.md).

## Commands

Run these in Minecraft chat after configuring the command path below.
Durations are seconds, default to 300, and must be between 1 and 3600.

| Command | What it does | Setup |
| --- | --- | --- |
| `\automine cobblestone 120` | Mines visible, reachable blocks matching exactly that block ID | Hold the correct tool. Useful at a cobblestone generator or beside exposed ore. |
| `\farm 300` | Harvests and replants mature wheat, carrots, potatoes, and beetroot within reach | Put matching seeds/carrots/potatoes in the hotbar. Crops without planting supplies are skipped. |
| `\shear 300` | Aims at and shears nearby sheep, with a cooldown | Hold shears and stand inside a sheep pen. |
| `\autofish 300` | Casts, detects bobber dips, reels in, and recasts | Hold a fishing rod, reel it in first, and aim at open water away from other fishing players. |

You can use a full block ID: `\automine minecraft:deepslate_iron_ore 120`.
These commands stay in place. They do not navigate, collect scattered drops,
store inventory, or replace worn tools. `farm` changes your selected hotbar
slot to the appropriate planting item. Keep room in your inventory and
monitor tool durability. Run one automation at a time.

## Installation

1. Install Minescript 5.0 and Python 3.10+.
2. Keep this repository in `minescript/Minescript-Library`.
3. On Windows, add this to `minescript/config.txt`, preserving other custom paths:

   ```text
   command_path=.;Minescript-Library;system/exec
   ```

4. Ensure the `python` setting points to a working Python executable.
5. Restart Minecraft if commands are not listed by `\ls`.

Alternatively, copy the five root `.py` files into the `minescript` directory,
keeping the license notices with your copy. Do not copy `upstream` snapshots
or the test module as runnable game commands. No pip packages or Minescript
Plus add-ons are required to use the commands.

See the official [Minescript configuration reference](https://minescript.net/docs/#configuration).

## Stopping and safeguards

Press **F8** or open a menu/chat to stop. Sessions also stop on damage, low
health, world/dimension changes, and their time limit. Inputs and event
listeners are released on normal completion and Python exceptions. A forced
process termination can bypass Python cleanup; Minescript's built-in
`\killjob -1` stops all jobs if needed.

Mining checks the actual crosshair block before and during attack, skips the
floor directly beneath your feet, and avoids attacking when an entity is
targeted. It does not assess cave safety, falling blocks, fluids, or tool
suitability. `farm` checks maturity and hotbar planting supplies, then stops
if it cannot verify replanting. Fishing binds a newly appearing nearby
bobber, but the API does not establish ownership; use it away from others.

These are survival interactions, so cheats or operator permissions are not
required. Use automation where your world's or server's rules permit it.
No script sends network requests, reads credentials, sells items, or runs
shell commands.

## Verification

Offline regression tests use a fake Minescript bridge and never control a
game. They cover stop conditions, cleanup after errors, occluded blocks,
entity interference, crop maturity, seed requirements, replant failure,
negative coordinates, and bobber selection:

```text
python -m pytest -q
```

Install `pytest` only for development. Syntax, lint, static types against the
installed Minescript API, security checks, and offline tests were checked
during setup. Live harvesting, shearing, mining, and fishing in Minecraft
still need an in-game trial; offline tests cannot prove those interactions.

Setup verification: 41 offline tests passed, with 92% statement coverage.
The production scripts passed Ruff, Pyright against the local Minescript
5.0 API, and Bandit without findings.
