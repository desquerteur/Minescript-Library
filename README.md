# Minescript-Library

Eight MIT-licensed scripts for mining, farming, and checking your supplies
in Minecraft. Requires Minescript 5.0 and Python 3.10 or later. Six community
scripts were adapted, and two automation helpers were added for this
collection. Credits, original snapshots, and upstream licenses are recorded
in [SOURCES.md](SOURCES.md).

## Script catalog

### Mining and farming

Run these in Minecraft chat after configuring the command path below.
Durations are seconds, default to 300, and must be between 1 and 3600.

| Script name | Example command | What it does | Setup |
| --- | --- | --- | --- |
| [automine.py](automine.py) | `\automine cobblestone 120` | Mines visible, reachable blocks matching exactly that block ID. Useful at a cobblestone generator or beside exposed ore. | Hold the correct tool. |
| [farm.py](farm.py) | `\farm 300` | Harvests and replants fully grown wheat, carrots, potatoes, and beetroot within reach. | Put the corresponding seeds, carrots, or potatoes in the hotbar. Crops without planting supplies are skipped. |
| [shear.py](shear.py) | `\shear 300` | Aims at and shears nearby sheep, with a cooldown between attempts. | Hold shears and stand inside a sheep pen. |
| [autofish.py](autofish.py) | `\autofish 300` | Casts a fishing rod, detects bobber dips, reels in, and recasts. | Hold a fishing rod, reel it in first, and aim at open water away from other fishing players. |

You can use a full block ID: `\automine minecraft:deepslate_iron_ore 120`.
These commands stay in place. They do not navigate, collect scattered drops,
store inventory, or replace worn tools. `farm` changes your selected hotbar
slot to the appropriate planting item. Keep room in your inventory and
monitor tool durability. Run one automation at a time.

### Inventory and world tools

These four tools print information in your local Minecraft chat and finish
immediately. They do not press keys or change blocks and entities.

| Script name | Example command | What it does | Options |
| --- | --- | --- | --- |
| [inventory.py](inventory.py) | `\inventory wheat` | Totals matching items across your main inventory and hotbar, and shows used/free slots. Useful for checking seeds, crops, or mined resources. | Omit the filter to list all item types. Armor and offhand slots are excluded. Filters ignore case. |
| [nearby.py](nearby.py) | `\nearby 16 sheep` | Lists nearby loaded animals, players, or dropped items with their distance and coordinates. | Radius defaults to 16 blocks; allowed range is 1–64. Optional name/type filter. Shows up to 20 matches. Example for drops: `\nearby 16 item`. |
| [entityinfo.py](entityinfo.py) | `\entityinfo 6` | Shows the name, type, position, available health, and UUID of the entity in your crosshair. | Range defaults to 6 blocks; allowed range is 1–64. Look directly at the entity. |
| [diagnose.py](diagnose.py) | `\diagnose` | Displays Minecraft, Minescript, Python, mod loader, and operating system versions to help troubleshoot script setup. | No arguments. Displays no configuration file contents and writes no report file. |

[automation_common.py](automation_common.py) is the shared helper used by the
commands. Keep it beside the other scripts; it is not a standalone command.
The `upstream/` folder contains reference snapshots, and `licenses/` contains
the original authors' license notices.

## Installation

1. Install Minescript 5.0 and Python 3.10+.
2. Keep this repository in `minescript/Minescript-Library`.
3. On Windows, add this to `minescript/config.txt`, preserving other custom paths:

   ```text
   command_path=.;Minescript-Library;system/exec
   ```

4. Ensure the `python` setting points to a working Python executable.
5. Restart Minecraft if commands are not listed by `\ls`, then run `\diagnose`
   to check that the library can run.

Alternatively, copy all root `.py` files into the `minescript` directory,
keeping the license notices with your copy. Do not copy `upstream` snapshots
or the test module as runnable game commands. No pip packages or Minescript
Plus add-ons are required to use the commands.

See the official [Minescript configuration reference](https://minescript.net/docs/#configuration).

## Stopping and safeguards

For the four automation scripts, press **F8** or open a menu/chat to stop.
Sessions also stop on damage, low health, world/dimension changes, and their
time limit. Inputs and event listeners are released on normal completion and
Python exceptions. A forced
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

Tests also cover inventory slot boundaries, nearby-result limits, invalid
tool arguments, diagnostics output, and README coverage of every script.
Latest verification: 54 tests passed, with 92% statement coverage across the
scripts and shared helper. Ruff, Pyright against the local Minescript 5.0
API, and Bandit passed without findings.
