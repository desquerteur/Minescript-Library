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

For example, `\travel_elytra 1 1` means **X=1, Z=1**, with surface height chosen
automatically. The resolved destination is printed with X/Y/Z labels before
travel starts, including during `--check`. The selected landing patch is shown
separately, with its distance from the original destination; a nearby touchdown
is followed by walking to the original point. After touchdown, the script briefly
waits for grounded position and momentum to settle before handing over to walking.
If walking cannot start, it prints the actual position and the unchanged goal.

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

Walking pauses to eat and looks away from interactive blocks. While swimming,
it keeps the float control held during eating so that the pause does not make
the player sink. In flight,
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

Start on the ground on full blocks, or in open water. The local pathfinder works around nearby
obstacles and handles one-block rises and drops. It **holds forward continuously
on clear, level stretches**, checks the next few steps while moving, and reports
remaining distance. Straight routes retain a checked buffer so local route
refreshes can finish without releasing forward. Eating, blocked terrain, route
ends, and precise elevation changes can pause walking.

Open diagonal paths use diagonal steps with both adjoining cells checked; the
traveler does not need to zigzag between cardinal directions on open ground.
Off-center starts first align with the next waypoint while keeping forward held.
If a delayed position update crosses several known route cells, the controller
resumes from that cell instead of declaring the player off-route.

The current terrain model recognizes common full blocks, double slabs, and
non-colliding plants. It also plans across open **water surfaces**, including
deep water where there is no reachable riverbed. It rejects lava, powder snow,
cactus/fire hazards, unknown floors, and unsupported shapes. It does not dig, build bridges,
climb ladders, open doors, or handle half slabs/stairs. Detours that extend
beyond the local scan may need a manual intermediate destination.

For rivers and lakes, the bot holds forward and the float control, stays at the
surface, and resumes walking on a reachable bank. It can leave water onto a
bank up to one block higher. Water plants such as kelp and seagrass are accepted.
Surface movement uses a floating height rather than requiring feet to remain
exactly at an integer block height. If it starts submerged, it first attempts
to surface; it searches up to 16 blocks above for an open surface and gives the
ascent up to 12 seconds. Roofed/under-ice water, downward waterfalls, bubble
columns, and underwater destinations are not supported routes. Use `X Z` if
you do not know the destination surface height. Flight landing pads still
require dry solid ground.

It stops after repeated blocked steps or 90 seconds without sustained distance
progress, rather than pushing against the same obstacle indefinitely.

## Elytra

Wear an Elytra with **more than 60 durability remaining**. Carry **plain firework
rockets without explosion stars**. Rockets and food can be in any normal carried
inventory slot. Keep a clear outdoor takeoff corridor and sufficient food/fuel.

The script selects a rocket before jumping. A callback inside the game opens
the wings using Minecraft's normal eligibility check and glide request, then
uses one rocket on the same game tick. This removes the Python round trips
between opening the wings and boosting. The callback also watches for F8,
menus, damage, and world changes, and is removed after launch. Active Creative
flight must be turned off first. An already-gliding or airborne player is accepted.

**Rocket-saving is the default.** A single rocket powers a climb, followed by a
shallow glide that spends the gained altitude. Another rocket is requested only
when altitude runs low and the previous climb has ended. There is no periodic
four-second boost. Rocket duration is read from the held item, explosive rockets
are rejected again inside the game, and each use is a single item action. The
flight report includes the number of accepted rocket uses.

The altitude reference is 50 blocks above the higher of the start and requested
destination, capped at Y=310; `--height 80` raises that reference. Renewed climbs
normally start 25 blocks below it. This is an altitude budget, not a guarantee
of terrain clearance or a complete three-dimensional route.

Landing searches loaded surface heights within **24 blocks** of the destination
for a **dry, clear 5×5 patch**. For `X Y Z`, the patch must be at that feet height;
`X Z` chooses a surface height automatically. If the goal area is unsuitable,
the script also tries near the current flight position. It lets any active
rocket finish, then chooses steering and pitch from a short motion prediction
that accounts for inertia and braking before touchdown. This model assumes
normal gravity and no movement effects. On touchdown, walking finishes the
trip to the original coordinates, including correctly resolved relative coordinates.
Low fuel/wing durability triggers an earlier landing attempt.

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
food selection/verification, input cleanup, the shipped launch callback, rocket
checks, flight-controller transitions, landing-area selection, and the handoff
to walking. Landing feedback is also exercised in a simplified unboosted flight
model at different update intervals. These checks do not establish live Minecraft
launch or landing reliability; server behavior, collisions, and movement effects
still require in-game testing.

The optional Java bridge test runs the shipped surface lookup through the real
Pyjinn interpreter against Java methods with Minecraft's `int` signatures. It
checks negative coordinates, unloaded chunks, and coordinates near the world
border. To enable it, set `MINESCRIPT_TEST_CLASSPATH` to the installed Pyjinn and
Gson jars joined by your platform's classpath separator, and optionally set
`MINESCRIPT_TEST_JAVA` to a JDK's `java` executable. Without that classpath, this
test is skipped. It does not connect to Minecraft.
