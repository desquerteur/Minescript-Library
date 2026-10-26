# Minescript travel

Two original MIT scripts for the installed **Minecraft 26.3 / Minescript 5.0**
setup: walking and rocket-assisted Elytra travel, both with automatic eating.
The previous community collection has been removed.

**Status:** initial implementation with offline regression tests. Live Minecraft
validation is outstanding. Elytra steering, takeoff, and landing are experimental;
try them in a separate creative test world before a survival trip.

## Commands

Enter these in Minecraft chat. Use a **backslash** before the command.

| Script | Command | What it does |
| --- | --- | --- |
| [travel.py](travel.py) | `\travel 1200 -500` | Walk toward X=1200, Z=-500, following reachable terrain. |
| [travel.py](travel.py) | `\travel 1200 64 -500` | Walk to those coordinates, including the requested feet height. |
| [travel_elytra.py](travel_elytra.py) | `\travel_elytra 1200 -500` | Fly toward X/Z, choose a nearby landing surface, then finish on foot. |
| [travel_elytra.py](travel_elytra.py) | `\travel_elytra 1200 64 -500` | Fly toward a landing area at the requested feet height, then finish on foot. |

Use `X Z` when you do not know the surface height. `X Y Z` expects a reachable
feet height, not an underground or midair point. Relative coordinates work:
`\travel ~100 ~-200` or `\travel ~100 ~ ~-200`.

There is no overall time or distance limit. Commands finish on arrival, on a
stop request, or when they cannot continue. Run one traveler at a time.

## Check the setup before moving

```text
\travel 1200 -500 --check
\travel_elytra 1200 -500 --check
```

`--check` reads the setup without moving, eating, changing the selected item,
or firing rockets. Walking also checks for a local route. Flight reports
hunger, equipped-wing durability, and available plain rockets; takeoff and
landing terrain are checked during the journey. This is not a live flight test.

Remove `--check` to start. `\travel --help` and `\travel_elytra --help` show options.

## Food and stopping

Carry ordinary food in the hotbar **or main inventory**. At **14/20 hunger
points** or below, the traveler eats until it has at least 18 points, verifies
that hunger increased, and restores the previously selected hotbar slot.
Change the trigger with `--eat-at 16`, for example.

Food in main storage may be swapped into the hotbar; the displaced item stays
in the inventory. Food is not sorted back into its original storage slot.
Cooked meat/fish, bread, baked potatoes, golden carrots, apples, carrots,
beetroot, potatoes, melon, berries, cookies, and dried kelp are supported.
Harmful food, chorus fruit, potions, and golden apples are excluded.

Walking pauses to eat and looks away from interactive blocks. In flight,
steering continues while eating. If food runs out during flight, the controller
attempts a nearby landing; if no landing area is found, it returns control.

- **F8** or opening chat/a menu releases the travel controls.
- `\killjob -1` terminates all Minescript jobs.
- Damage, low health, a dimension change, and unrecoverable travel errors also
  return control. The scripts release their buttons when leaving normally or
  through Python exceptions.
- **Stopping the Elytra script does not stop your momentum or land you.**
  Take control immediately if still airborne. Minecraft must be responsive for
  stop controls and steering to work.

## Walking

Start on the ground, on full blocks. The local pathfinder works around nearby
obstacles and handles one-block rises and drops. It **holds forward continuously
on clear, level stretches**, checks the next few steps while moving, and reports
remaining distance. Straight routes retain a checked buffer so local route
refreshes can finish without releasing forward. Eating, blocked terrain, route
ends, and precise elevation changes can pause walking.

Open diagonal paths use diagonal steps with both adjoining cells checked; the
traveler does not need to zigzag between cardinal directions on open ground.

The current terrain model recognizes common full blocks, double slabs, and
non-colliding plants. It rejects liquids, powder snow, cactus/fire hazards,
unknown floors, and unsupported shapes. It does not dig, build bridges, swim,
climb ladders, open doors, or handle half slabs/stairs. Detours that extend
beyond the local scan may need a manual intermediate destination.

It stops after repeated blocked steps or 90 seconds without sustained distance
progress, rather than pushing against the same obstacle indefinitely.

## Elytra

Wear an Elytra with **more than 60 durability remaining**. Carry **plain firework
rockets without explosion stars**. Rockets and food can be in any normal carried
inventory slot. Keep a clear outdoor takeoff corridor and sufficient food/fuel.

The script checks the launch corridor, jumps once, waits until airborne, opens
the wings using Minecraft's normal glide request, and confirms that gliding
stays active before using a rocket. It also accepts an already-gliding or
airborne player. Active Creative flight must be turned off first; the script
does not change your game mode. A blocked jump and a refused glide now produce
different messages. `--check` also shows these flight states. Default cruise
height is 50 blocks above the higher of the start and requested destination,
capped at Y=310; `--height 80` changes that clearance target. This is a target,
not a guarantee of terrain clearance or a complete three-dimensional route.

It periodically boosts, steers, scans ahead for blocks, and begins a landing
approach near the destination. A **flat, clear 9×9 pad** must exist within four
blocks of the requested X/Z. For `X Y Z`, the pad must be at that feet height.
For `X Z`, it searches downward for a suitable surface. On touchdown it uses the
walking engine for the last part of the trip. Low fuel/wing durability triggers
an earlier landing attempt and then walking toward the original destination.

Dense forest, enclosed spaces, Nether ceilings, unloaded terrain, uneven landing
areas, lag, and strong effects on movement can exceed this controller's ability.
Immediate obstacles, failed gliding, or an unsuccessful landing attempt return
control instead of claiming arrival. The flight controller is not a substitute
for an in-game tested navigation mod.

## Installation

Keep this folder at `minescript/Minescript-Library`. In `minescript/config.txt`:

```text
command_path=.;Minescript-Library;system/exec
```

Your existing Python interpreter setting is retained. These scripts import the
installed `minescript` and `java` modules; no additional navigation mod or Python
package is required at runtime. [travel_common.py](travel_common.py) is a helper
module, not another command. API reference: [Minescript 5.0 documentation](https://minescript.net/docs/).

## Development checks

```text
python -m pytest -q
python -m pytest --cov=travel --cov=travel_common --cov=travel_elytra
```

Tests use a fake game bridge. They check pathfinding, simulated ground travel,
food selection/verification, input cleanup, rocket checks, flight-controller
transitions, landing-area selection, and the handoff to walking. They do not
simulate Minecraft flight physics or establish real-world landing reliability.
