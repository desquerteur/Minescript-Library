# Minescript travel

Walking, surface swimming, and rocket-saving Elytra travel with automatic eating,
built for **Minecraft 26.3 / Minescript 5.0**. The two commands are original
scripts distributed under the repository's [MIT license](LICENSE).

**[Read the complete travel guide →](docs/TRAVEL.md)**

## Quick start

Keep the three Python files together in `minescript/Minescript-Library`. Add the
folder to `minescript/config.txt`, retaining your working Python setting:

```text
command_path=.;Minescript-Library;system/exec
```

Join a world, stand on supported ground, and carry ordinary food in your hotbar
or main inventory. Enter commands in **Minecraft chat**, with a **backslash**:

```text
\travel 1000 500 --check
\travel 1000 500
```

The first command checks the setup and a local route without moving. The second
starts travel. Two coordinates mean **X Z**; three mean **X Y Z**, where Y is feet
height. `Y=surface` in chat means no particular destination Y was supplied.

## Commands

| Command | Purpose |
| --- | --- |
| `\travel 1000 500` | Walk/swim to X=1000, Z=500 along reachable terrain. |
| `\travel 1000 67 500` | Also require destination feet Y=67. |
| `\travel ~100 ~-50` | Move toward a goal offset from the command's starting X/Z. |
| `\travel_elytra 1000 500` | Cruise above the dimension's build limit, land nearby, then finish at the original goal on foot. |
| `\travel_elytra 1000 500 --height 80` | Override the default build-limit cruise with an 80-block altitude reference above start/goal. |
| `\travel 1000 500 --eat-at 16` | Eat at 16/20 hunger points or below; the default is 14. Both commands support this option. |
| `\travel 1000 500 --check` | Check without starting movement. Both commands support `--check`. |
| `\travel --help` / `\travel_elytra --help` | Print the built-in options. |

Elytra travel requires equipped wings with **more than 60 durability**, plain
rockets **without explosion stars**, food, and an open launch corridor. There is
no overall trip time limit. Run one traveler at a time.

## Full documentation

| Topic | Guide |
| --- | --- |
| First trip | [Walking and Elytra quick starts](docs/TRAVEL.md#quick-start) |
| Setup or update | [Requirements, folder layout, and loading changes](docs/TRAVEL.md#installation-and-updates) |
| Every flag | [Command reference](docs/TRAVEL.md#command-reference) |
| X/Z, X/Y/Z, `~`, and arrival tolerances | [Coordinates and arrival](docs/TRAVEL.md#coordinates-and-arrival) |
| Continuous walking, obstacles, steps, and detours | [Walking](docs/TRAVEL.md#walking) |
| Rivers, lakes, and banks | [Swimming](docs/TRAVEL.md#swimming) |
| Hunger thresholds, inventory behavior, and every supported food | [Automatic eating](docs/TRAVEL.md#automatic-eating) |
| Launch, rocket saving, height, and landing | [Elytra travel](docs/TRAVEL.md#elytra-travel) |
| F8, menus, job termination, and restarting | [Stopping and restarting](docs/TRAVEL.md#stopping-and-restarting) |
| Target versus landing spot, and what `Done` means | [Chat messages](docs/TRAVEL.md#reading-chat-messages) |
| Error messages and recovery steps | [Troubleshooting](docs/TRAVEL.md#troubleshooting) |
| Unsupported terrain and actions | [Limits](docs/TRAVEL.md#limits) |
| Source layout, tests, and real Pyjinn checks | [Development and verification](docs/TRAVEL.md#development-and-verification) |

## Movement and stopping

Walking follows larger, body-width checked corridors and holds forward on clear
stretches. Tight ground approaches can slow down; uncertain terrain and delayed
updates can trigger a brake. Swimming keeps flotation active, including while
eating. Elytra uses climb/glide cycles to conserve rockets, reports its chosen
landing spot, and retains the original coordinates for the walking finish.

Press **F8**, or open chat/a game menu, to stop. Closing the menu does not resume
the job. `\killjob -1` terminates **all** Minescript jobs. Damage, low health,
world/dimension changes, and unrecoverable route failures also return control.
**Stopping an Elytra job does not cancel flight momentum or land you.**

These are local client-side helpers, not a complete world navigation mod. They
do not dig, bridge, open doors, or guarantee a route across every terrain or
server condition. See the guide's [limits](docs/TRAVEL.md#limits).

## Development checks

```text
python -m pytest -q
python -m pytest --cov=travel --cov=travel_common --cov=travel_elytra
```

The normal suite uses offline game/geometry models. Optional tests use the real
Pyjinn interpreter with Java fixtures; [configuration and scope](docs/TRAVEL.md#development-and-verification)
are documented in the guide. Neither replaces live testing after movement changes.

The runtime files are [travel.py](travel.py), [travel_elytra.py](travel_elytra.py),
and the shared helper [travel_common.py](travel_common.py). No additional
navigation mod or Python package is required at runtime. API reference:
[Minescript API documentation](https://minescript.net/docs/).
