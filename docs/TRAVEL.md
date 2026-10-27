# Travel guide

Complete player guide for `\travel` and `\travel_elytra`, built for the installed
**Minecraft 26.3 / Minescript 5.0** setup. Both commands can eat automatically.
The scripts are original code distributed under the repository's MIT license.

[Back to the project README](../README.md)

## Contents

- [Quick start](#quick-start)
- [Installation and updates](#installation-and-updates)
- [Command reference](#command-reference)
- [Coordinates and arrival](#coordinates-and-arrival)
- [Walking](#walking)
- [Swimming](#swimming)
- [Automatic eating](#automatic-eating)
- [Elytra travel](#elytra-travel)
- [Stopping and restarting](#stopping-and-restarting)
- [Reading chat messages](#reading-chat-messages)
- [Troubleshooting](#troubleshooting)
- [Limits](#limits)
- [Development and verification](#development-and-verification)

## Quick start

### Your first walking trip

1. Join your world in the Minecraft instance that has Minescript installed.
2. Stand on ordinary full blocks, with an open stretch ahead. Carry supported
   food in your hotbar or main inventory.
3. Open Minecraft chat and enter this command, including the backslash:

   ```text
   \travel ~16 ~ --check
   ```

4. Read the printed destination and local route check. Two coordinates mean
   **X and Z**. This example chooses a point 16 blocks farther along positive X,
   retaining your starting Z. It does not move you.
5. Without changing your starting position, start the trip:

   ```text
   \travel ~16 ~
   ```

6. The bot follows the route and reports arrival. Press **F8** to stop early.

`--check` examines the setup and a local walking route. It does not check every
block of a long journey or guarantee that food will last until arrival.

### Your first Elytra trip

1. Equip an Elytra with **more than 60 durability remaining**.
2. Carry plain firework rockets **without explosion stars**, plus supported food.
3. Stand outside with clear overhead space and an open launch corridor. If
   Creative flight is active, land and turn that flight ability off first.
4. Choose a destination and check the equipment:

   ```text
   \travel_elytra 1000 500 --check
   ```

5. Remove `--check` to launch:

   ```text
   \travel_elytra 1000 500
   ```

The bot climbs using a rocket, glides to conserve rockets, chooses a nearby
landing patch, and finishes on foot. Its landing patch and your original
destination are printed separately. The flight check is an equipment/state
check; takeoff and landing terrain are inspected during the trip.

**Stopping a flight releases the controls but does not remove momentum or land
the player.** Take over if you stop while airborne.

## Installation and updates

### Requirements

| Requirement | Details |
| --- | --- |
| Minecraft instance | The client code targets Minecraft 26.3. Other versions are not verified. |
| Minescript | Version 5.0, including its installed `java` bridge and Pyjinn support. |
| Python | Python 3.10 or newer, configured in Minescript. The current local setup uses Python 3.13. |
| World | Join a world before running either command. |
| Extra navigation mod | None required. |
| Python packages for players | None beyond the installed Minescript environment. Development tools are separate. |

### Folder layout

Keep all three Python files together:

```text
<Minecraft instance>/
  minescript/
    config.txt
    Minescript-Library/
      travel.py
      travel_elytra.py
      travel_common.py
      README.md
      docs/
        TRAVEL.md
```

In `minescript/config.txt`, include the library in the command search path:

```text
command_path=.;Minescript-Library;system/exec
```

Keep your working `python=` setting. If Python cannot be started, that setting
must point to your actual installed Python executable.

`travel_common.py` is a shared helper, not another travel command. Elytra travel
also imports the walking engine, so install/update the three scripts together.
Minescript's `system` folder is supplied by the mod and remains separate.

### Loading an update

Stop the running traveler, update the repository or replace the three scripts
as a set, and start a new command. An already-running Python job keeps the code
it loaded at startup. Updating files does not change that running job.

If old behavior persists after starting a new job, check the Minecraft instance
and look for older copies of `travel.py` or `travel_elytra.py` earlier in
`command_path`. With the example setting, the top-level `minescript` directory
is searched before `Minescript-Library`.

## Command reference

Enter these commands **in Minecraft chat**, not in PowerShell or a server
console. Use `\travel`, with a backslash, rather than `/travel`.

### Syntax

```text
\travel X Z [--eat-at POINTS] [--check]
\travel X Y Z [--eat-at POINTS] [--check]
\travel_elytra X Z [--height BLOCKS] [--eat-at POINTS] [--check]
\travel_elytra X Y Z [--height BLOCKS] [--eat-at POINTS] [--check]
```

The square brackets describe optional arguments; do not type them. Replace
`X`, `Y`, `Z`, `POINTS`, and `BLOCKS` with numbers. Put coordinates first and
options afterward, as in the examples.

### Options

| Option | Commands | Default | Accepted values | Meaning |
| --- | --- | --- | --- | --- |
| `--eat-at POINTS` | Both | `14` | Integers `1` through `19` | Start eating when hunger is at or below this many points out of 20. |
| `--check` | Both | Off | No value | Check without moving, eating, selecting an item, or using rockets. Walking checks a local route; Elytra reports equipment and flight state. |
| `--height BLOCKS` | Elytra only | Dimension build limit + 8 | Integers `25` through `120` | Optional lower-altitude override: reference above the higher of start and explicit destination Y, capped at build limit + 8. Omit to cruise above the build limit. |
| `--help` or `-h` | Both | — | No value | Print the command's built-in help without starting travel. |

There is no overall trip duration or distance option. There is also no sprint,
speed, pause/resume, saved-route, or waypoint-list option. Route checks and
individual actions have their own failure limits.

### Copyable examples

```text
\travel 1000 500
\travel 1000 67 500
\travel -1200.5 600.25
\travel ~100 ~-50
\travel ~100 ~ ~-50
\travel 1000 500 --eat-at 16
\travel 1000 500 --check
\travel --help
\travel_elytra 1000 500
\travel_elytra 1000 67 500
\travel_elytra ~200 ~
\travel_elytra 1000 500 --height 80 --eat-at 16
\travel_elytra 1000 500 --check
\travel_elytra --help
```

Run **one traveler at a time**. Walking and Elytra jobs share the same controls.

## Coordinates and arrival

### Coordinate order

| Input | Interpretation |
| --- | --- |
| `\travel 1 1` | X=1, Z=1; no required destination Y. |
| `\travel 1 67 1` | X=1, feet Y=67, Z=1. |
| `\travel_elytra 1 1` | Fly toward X=1, Z=1, choose a landing surface, then walk to the goal. |
| `\travel_elytra 1 67 1` | Search for a landing patch at feet Y=67 near X=1, Z=1, then finish on foot. |

The printed `Y=surface` means no particular destination height was supplied.
Use this form for ordinary overland trips when you do not know the ground
height. It does not mean Y=0 or sea level, and it does not make the bot dig to
an underground point.

With three coordinates, Y is the **player's feet height**. An unreachable Y can
prevent arrival even when X/Z are correct. A midair point, enclosed cave, or
unsupported ledge is not made reachable by supplying its coordinates.

### Absolute and relative values

Numbers without `~` are absolute. A tilde adds an offset to the position where
that command starts. A bare `~` keeps the corresponding starting coordinate.
Absolute and relative values can be mixed.

For a starting position **X=100, Y=64, Z=−200**:

| Command | Resolved destination |
| --- | --- |
| `\travel 1000 500` | X=1000, Z=500, any reachable destination height. |
| `\travel ~100 ~-50` | X=200, Z=−250, no required Y. |
| `\travel ~ ~ ~100` | X=100, Y=64, Z=−100. |
| `\travel ~100 70 ~-50` | X=200, Y=70, Z=−250. |

In particular, the middle `~` in a three-coordinate command **locks the goal
to the starting feet height**. Omit Y entirely if you want an ordinary surface
destination.

Relative coordinates are resolved once for the trip. Elytra's walking handoff
uses that same resolved destination. If you stop and rerun a relative command
from a different position, it creates a different destination. Use the printed
absolute X/Z, and Y if required, to return to the original goal.

Coordinates belong to the **current dimension**. The bot does not convert
Overworld/Nether coordinates or navigate portals. A world/dimension change
ends the current trip.

### Precision and input bounds

- Ordinary decimal coordinates are accepted; use a dot as the decimal separator.
- Arrival allows up to **0.85 blocks of horizontal distance** from the point.
  When Y is specified, ordinary ground arrival also allows **0.3 blocks of
  vertical difference**. Water-surface arrival has a separate floating-height
  allowance.
- Input validation accepts X/Z up to an absolute value of `29999000`, and an
  explicit Y from `-2048` to `2048`. These are parser limits, not promises that
  those heights or locations exist or are reachable in the current world.
- The destination is printed to three decimal places for readability; this
  display does not round the stored destination.

## Walking

### How movement works

The pathfinder examines nearby loaded terrain and chooses a route toward the
destination. For distant goals, intermediate targets follow the goal's bearing.
The walker keeps larger, committed aim points instead of repeatedly aiming at
each block center.

On a clear stretch it holds forward continuously. A shortcut is accepted only
when the player's **0.6-block width plus a small margin** fits along the whole
segment, with suitable support and headroom. It cannot treat a clear center
line as permission to clip a wall or cut across a hole with one side of the body.

Nearby terrain is refreshed while walking. The controller can keep moving
during a route refresh when checked ground remains ahead. A short movement
permission also runs inside the game: if Python stalls or fails to renew the
checked distance, forward is released. Distance already traveled during a
delayed call is deducted before another permission is accepted.

Near a tight ground approach, the bot can crouch to slow down. It can pause for
food, an obstruction, an expired movement permission, or an unsupported
transition. Continuous movement applies to clear routes; it is not a promise
to keep walking when the next step is uncertain.

### Terrain support

| Terrain/action | Behavior |
| --- | --- |
| Solid terrain | Reads Minecraft's collision shapes, so full floors do not depend on a block-name list. Flat full-width shapes with tops between 0.8 and 1 block are accepted too, including farmland/path blocks. |
| Clear diagonal/angled paths | Uses body-width checked shortcuts rather than one-block zigzags. |
| One-block rise | Checks the transition and uses one jump. Space beyond the step can allow continued forward movement. |
| One-block drop | Can follow a checked downward transition. Larger drops are not planned as walking edges. |
| Open water surface | Can swim and leave onto a reachable bank. See [Swimming](#swimming). |
| Non-colliding plants | Uses the game's empty collision shape and empty fluid state, with separate hazard exclusions. New plant names no longer require adding them to a walking whitelist. |
| Double slabs | Recognized as full-height support. |
| Bottom slabs, stair shapes, ladders | Not supported by the route model. Upper slabs with a verified full-width top can act as floors. |
| Lava, fire, cactus, powder snow | Rejected as route hazards. |
| Magma, honey, slime blocks | Intentionally excluded as supporting floors. |
| Unknown/unloaded support | Not treated as safe ground. |
| Doors, gates, digging, block placement | No automatic opening, breaking, bridging, or building. |

Walking reads loaded block states and collision traits together inside the game.
An unloaded chunk is blocked. Each fresh corridor scan replaces both the block
state and its collision result; a closed gate cannot retain its earlier open
result. This remains a conservative cell-based route model, rather than a full
solver for every partial shape. Normal walking speed is assumed. Movement effects,
entities pushing/blocking the player, server corrections, and changes outside
the client's loaded data can require manual control.

### Game-tick walking control

The Python planner approves a body-width corridor and a bounded movement distance.
Inside the game, each tick checks actual movement against that distance and keeps
the camera aimed along the approved span. It releases forward before the checked
distance runs out, even when the Python loop is delayed. A separate expiry timer
also bounds an unrenewed request. A safe expiry can be renewed; F8/menu cancellation
stays latched for the rest of that job.

Before eating, the walker stops its game-side controller. This prevents tick
steering from fighting the food-use orientation. After food is verified, the
route is checked again before movement resumes.

This is our own MIT implementation. Wurst's
[AutoWalk](https://github.com/Wurst-Imperium/Wurst7/blob/4fa258b7b339f1823e73ae8455c404209e3690cd/src/main/java/net/wurstclient/hacks/AutoWalkHack.java)
holds forward, while its
[GoTo](https://github.com/Wurst-Imperium/Wurst7/blob/4fa258b7b339f1823e73ae8455c404209e3690cd/src/main/java/net/wurstclient/commands/GoToCmd.java)
and
[WalkPathProcessor](https://github.com/Wurst-Imperium/Wurst7/blob/4fa258b7b339f1823e73ae8455c404209e3690cd/src/main/java/net/wurstclient/ai/WalkPathProcessor.java)
provided reference points for separating path planning and movement updates.
No Wurst source or Wurst installation is included or required. Ladders, mining,
larger falls, and Wurst-specific abilities have not been added.

### Long trips and detours

There is no overall time limit. The local scan moves along with the player as
the trip progresses. It is not a map of the entire route in advance.

An obstacle may require a detour that temporarily increases the displayed
distance. That distance is straight-line X/Z distance, not remaining path length.
Very large walls, cliffs, or maze-like obstacles can exceed the local planner.
In that case, travel to a reachable intermediate point, then start the next leg.

Repeatedly blocked route attempts stop the job. It also stops after **90 seconds
without sustained distance progress**, rather than continuing against the same
obstacle indefinitely.

## Swimming

The walking command also handles open river and lake surfaces. It does not
need a reachable riverbed: deep water is represented by its surface.

- Forward and the float control are held while swimming.
- The float control remains active while eating in water.
- On reaching dry, supported ground, ordinary walking resumes.
- A reachable bank can be up to one block higher.
- Kelp and seagrass are recognized as water plants.
- If starting submerged, the bot first tries to reach an open surface. It
  searches up to 16 blocks above and allows up to 12 seconds for the ascent.

Roofed water, under-ice routes, bubble columns, downward waterfalls, lava, and
underwater destinations are not supported swimming routes. The bot does not
plan an underwater expedition or seek air pockets. Use `X Z` when you do not
know the surface height.

## Automatic eating

### Trigger and target

Hunger uses **20 points**, corresponding to 10 full food icons. By default,
eating starts at **14/20 or below**. Change it with:

```text
\travel 1000 500 --eat-at 16
\travel_elytra 1000 500 --eat-at 16
```

The accepted trigger range is `1` through `19`. The bot eats until hunger is
at least `max(18, trigger + 1)`: normally 18 points, 19 for `--eat-at 18`, and
20 for `--eat-at 19`. It verifies that hunger actually rises rather than
assuming an item was consumed after a delay.

On land, movement pauses and the camera looks away from interactive blocks
while eating. In water, flotation stays active. During flight, steering
continues while food is being consumed.

### Supported food

Food must be in the **hotbar or main inventory**. The offhand, containers, and
modded storage are not searched. The supported food with the highest listed
hunger restoration is chosen first.

| Hunger points | Accepted foods |
| --- | --- |
| 8 | Steak (`cooked_beef`), cooked porkchop |
| 6 | Cooked mutton, cooked salmon, cooked chicken, golden carrot |
| 5 | Baked potato, bread, cooked rabbit, cooked cod |
| 4 | Apple |
| 3 | Carrot |
| 2 | Melon slice, sweet berries, glow berries, cookie |
| 1 | Beetroot, potato, dried kelp |

Golden apples, enchanted golden apples, chorus fruit, poisonous foods, potions,
and foods not in this table are excluded. A golden carrot is supported; a
golden apple is not.

Food in main storage can be swapped into the hotbar. The displaced item remains
in the inventory. The previously selected hotbar slot is restored afterward,
but items are not sorted back into their original storage positions.

If food is unavailable when needed, walking stops. During flight, missing food
triggers an attempted early landing. Walking afterward can still stop if food
is needed and has not been replenished. A failed consumption attempt times out
after six seconds without a hunger increase.

## Elytra travel

### Equipment and launch

Equip an Elytra with **more than 60 durability remaining**. Carry supported
food and **plain firework rockets without explosion stars** in the hotbar or
main inventory. The offhand is not searched for rockets.

The bot checks overhead space and the launch corridor, selects a rocket before
jumping, and uses Minecraft's normal eligibility check to open the wings.
Opening the wings and using the first rocket happen together inside the game
tick, avoiding Python round trips during the short airborne launch window.
The bot does not force Creative flight or change game mode.

An already-gliding or airborne player is accepted. If testing in Creative mode,
the mode itself can remain active, but the Creative **flying ability** must be
off before takeoff. An equipment check still requires usable wings and rockets.

### Rocket-saving flight

Rockets are controlled by altitude feedback:

1. One rocket powers a climb.
2. The bot switches to a shallow glide and spends the gained altitude.
3. Another rocket is requested when altitude runs low and the previous climb
   has ended. The default keeps a tight reserve above the build limit;
   an explicit `--height` permits a wider glide to save rockets.

There is no fixed four-second rocket loop. The duration of the held rocket is
read, explosive rockets are rejected again inside the game, and an individual
rocket use is a single item action. Different plain rocket durations are
accepted; a fixed distance per rocket is not promised.

The report counts **accepted rocket-use actions**. In Creative mode, that does
not necessarily mean the same number of inventory items was consumed.

### Height setting

```text
\travel_elytra 1000 500 --height 80
```

Without `--height`, the bot reads the current dimension's actual build limit
and targets **8 blocks above it**. In a standard Overworld this is **Y=328**,
above the first air level at Y=320. Renewed climbs begin below Y=324 once the
previous climb has ended. The clearance reserve avoids deliberately gliding
back into the buildable layer. Powered climbs no longer flatten at the old
fixed Y=300 threshold. The cruise target and build limit are printed on start.

An explicit `--height 80` instead requests 80 blocks above the higher of the
start and explicit destination Y; accepted values remain 25–120. That reference
is capped at the dimension's build limit plus 8, with renewed climbs normally
beginning 25 blocks below it.

Build-limit cruising can spend more rockets than a lower, wider glide.
Takeoff and landing still cross terrain, so obstacle checks remain active.
Neither profile is a constant-height lock or a complete three-dimensional
flight pathfinder. Short trips can enter the landing approach before reaching
the cruise target. Unusual physics or server restrictions can affect clearance.

### Approach, landing, and the walking finish

The normal landing search begins within **160 horizontal blocks** of the goal,
so high cruising does not request a destination surface hundreds of blocks
away in unloaded chunks. The bot searches loaded surface heights within
**24 blocks** of the requested
X/Z for a **dry, clear 5×5 patch**. With `X Y Z`, that patch must be at the
requested feet height. With `X Z`, it chooses a suitable surface height.

If the goal area is unsuitable, it also tries near the current flight position.
Low fuel, wings at 60 durability or below, or depleted food can trigger this
earlier landing attempt. If no usable patch is found, it returns control.

An active rocket is allowed to finish before the unboosted approach. Steering
uses a short motion prediction to account for inertia and braking. It assumes
ordinary gravity and no unusual movement effects.

**A nearby touchdown is not the final destination.** The printed landing spot
may differ from your goal. After touchdown, the bot allows up to three seconds
for position and momentum to settle on suitable ground, then uses the walking
engine to finish at the **original resolved coordinates**. Landing does not
recalculate relative coordinates from the touchdown point.

If the walking finish cannot start, the message includes the actual touchdown
position and the unchanged destination. If the final walking route is blocked,
the trip can stop even after a successful landing.

## Stopping and restarting

| Action/condition | Result |
| --- | --- |
| Press F8 | Ends the current traveler and releases its controls. |
| Open chat, inventory, or another game menu | Stops travel; closing the menu does not resume it. |
| Enter `\killjob -1` | Terminates **all** Minescript jobs, not only the traveler. |
| Take damage | The shared travel session stops and returns control. |
| Health is 6/20 or lower | Stops rather than continuing the trip. |
| Change world or dimension | Ends the current trip. |
| Start another traveler | The new command refuses while another travel job is active. |
| Unsafe or repeatedly blocked route | Replans where possible, otherwise stops with a reason. |

The scripts release forward, jump, sprint, crouch, use, and attack controls
during normal exception cleanup. The walking timer separately bounds forward
movement if Python stops renewing its checked route. Minecraft must remain
responsive for controls to work.

The travel scripts do not save or resume an ended trip. Once stopped, take
control, resolve the problem, and start a new trip. Rerun absolute coordinates
to keep the same goal. Rerunning `~` coordinates from a different location
creates a new goal.

If a job is still listed as active, Minescript's job tools can inspect and end
it. These commands are built into Minescript, rather than flags on `travel`:

```text
\jobs
\killjob 3
```

The example ends job **3 only**; replace `3` with the ID shown for the intended
job. Use `\killjob -1` only when you intend to terminate every Minescript job.
Minescript's process suspension tools are not a saved-trip feature of these
scripts; use the stopping/restarting workflow above for travel.

For Elytra, stopping does not cancel velocity or perform a landing. Fly or land
manually before trying an ordinary walking command.

## Reading chat messages

### Walking example

```text
Walking destination: X=1000.000, Y=surface, Z=500.000.
Travel started. F8 or opening chat/a menu releases travel controls.
Walking: 512 blocks to destination.
Hunger 14/20: eating before continuing.
Hunger 20/20: continuing travel.
Arrived at the walking destination.
```

The distance is horizontal straight-line distance. It can increase briefly
during a legitimate detour. `Y=surface` means no exact destination Y was required.

### Flight finish example

```text
Flight destination: X=1000.000, Y=surface, Z=500.000.
Flight: 512 blocks away; 2 rockets used; Elytra durability 220.
Landing spot: X=1000.500, Y=67.000, Z=500.500; 0.7 blocks from the destination.
Landing approach: rockets off. Walking will finish the remaining distance.
Landed. Letting movement settle before finishing on foot.
On ground at X=1000.420, Y=67.000, Z=498.900; 1.2 blocks left to X=1000.000, Y=surface, Z=500.000.
Walking destination: X=1000.000, Y=surface, Z=500.000.
```

These are illustrative messages, not a promised flight result. The final walking
phase can report arrival or a reason it cannot continue.

### Completion versus script termination

- `Arrived at the walking destination.` confirms that the walking goal was reached.
- `Already at the destination.` means the player was within the arrival tolerance.
- `Landed...` confirms touchdown, not completion of the original trip.
- Minescript's `[N] Done: ...` means the script ended. It can also appear after
  a handled stop or route failure, so **read the preceding message**.

## Troubleshooting

### Starting and coordinates

| Message/symptom | What to check or do |
| --- | --- |
| Command not found | Verify the folder name, `command_path`, active Minecraft instance, and leading backslash. |
| `No module named minescript` when double-clicking a file | Run it through Minecraft chat and Minescript, not directly in Windows. |
| `Use X Z or X Y Z...` | Supply exactly two or three coordinate values. Options come after them. |
| Invalid number / coordinate error | Use numbers or `~` offsets, a dot for decimals, and supported bounds. Do not type the example placeholders or brackets. |
| `Another traveler is active...` | Stop the existing job first. Do not run walking and Elytra control simultaneously. |
| `Start on the ground or in open surface water.` | Land before using `\travel`; use `\travel_elytra` for flight. |
| `Start on level full blocks...` | Move onto supported full-block terrain. Half slabs, stair shapes, or a transitional feet height can prevent routing. |
| X/Z look wrong | Read the labeled destination. Two inputs are X/Z; three are X/Y/Z. Check signs, dimension, and whether `~` was used. |
| Stops near the goal after landing | Compare the original goal, chosen landing spot, and actual touchdown. Read the walking-start or approach message before assuming the coordinates changed. |
| Cannot arrive with correct X/Z | An explicit Y may be unreachable. Use `X Z` if no exact height is required. |

### Walking, swimming, and food

| Message/symptom | What to check or do |
| --- | --- |
| `No walking/swimming route found locally...` | A wall, cliff, hazard, or unknown terrain blocks the local route. Move to supported terrain or use a reachable intermediate goal around the obstacle. |
| `Your starting floor, water surface or headroom is unsupported...` | The following detail identifies the rejected block and its X/Y/Z. Check that material, the room above the player, and whether water has an open surface. |
| `Walking is blocked after three route attempts...` | Read the appended obstruction or stalled-movement reason. The bot does not dig, open doors, or force a crossing. |
| `No sustained route progress for 90 seconds...` | The local planner is not finding useful progress. Split the journey into manual intermediate destinations. |
| Pauses or crouches briefly | It may be eating, approaching a tight spot, checking a transition, or braking after a delayed update. Check the preceding reason if it stops entirely. |
| `Player left the checked step...` / `Player dropped below the checked route...` | Take control. A transition, push, or position correction exceeded the checked route. Reposition before restarting. |
| `No open water surface or reachable bank found nearby...` | Check for an open surface or supported bank. Roofed water and unsupported fluid routes are not handled. |
| `Could not reach breathable surface water...` | Surface manually and restart. The automatic ascent has a limited search distance and time. |
| `No supported food left...` | Put a food from the supported table in the hotbar or main inventory. Offhand-only food does not count. |
| `Selected food did not appear in your hand...` | Check for inventory changes, full hotbar/swapping problems, or other scripts changing the selected item. |
| `Eating did not restore hunger...` | Check the held food, connection, and competing use controls. The bot stops after no verified hunger increase. |
| `Damage or low health detected...` | Deal with the danger or recover health manually before starting again. |

### Elytra and script errors

| Message/symptom | What to check or do |
| --- | --- |
| `Equip an Elytra in your chest slot first.` | Equip the wings, rather than only carrying them. |
| `Elytra needs more than 60 durability...` | Repair or replace the equipped wings before starting. |
| `Carry plain firework rockets...` | Put rockets without explosion stars in the hotbar or main inventory. |
| `Creative flight is active...` | Land and turn the Creative flying ability off. The script does not toggle it for you. |
| `Takeoff needs clear space overhead...` | Move outside, away from a roof, trees, or buildings. |
| `Jump did not leave the ground...` | Check the ceiling, water, riding state, and movement restrictions. |
| `Minecraft refused the glide or rocket...` | Take control; check wings, selected rockets, launch conditions, and server behavior. |
| `Elytra is not gliding; no rocket was used.` | The bot will not fire a flight rocket while not gliding. Inspect why flight ended. |
| `No dry, clear landing surface found within 24 blocks...` | Take over and choose an open dry landing area. Dense trees, water, or uneven ground may offer no suitable patch. |
| `Obstacle immediately ahead...` / `Landing approach obstructed...` | Take control of the flight. The approach is blocked; this is not an arrival message. |
| `Gliding ended unexpectedly...` | Take control and inspect equipment, contact with terrain, and flight state. |
| `Landing has not completed after 90 seconds...` | Finish the landing manually. |
| `Walking could not start after landing...` | Use the printed actual position and unchanged goal. Stand still on suitable full blocks, then retry the walking leg. |
| Traceback mentioning `mc.screen`, or `hasChunk(java.lang.Long, java.lang.Long)` | Those were addressed in earlier updates. Update all three scripts together, stop the old job, and start a new command; check for stale duplicate copies if the error persists. |
| Any new Python/Java traceback | Keep the exact command, labeled target, actual X/Y/Z, and the bottom of the traceback. The exception name and final cause are more useful than only the first traceback line. |

## Limits

These are client-side travel helpers, not a complete navigation mod. They use
loaded local terrain and normal movement assumptions. They do not provide:

- A full-world map or a guarantee that every destination is reachable.
- Automatic mining, bridging, block placement, door/gate operation, or portal use.
- General stair/half-slab, ladder, underwater, or arbitrary three-dimensional routing.
- Automatic Elytra repair/replacement, inventory resupply, or equipment sorting.
- Unattended recovery from combat, damage, death, unusual movement effects, or
  every server/physics correction.
- A persistent saved trip that resumes after menus, disconnects, or restarting Minecraft.

Support for a route does not guarantee safe behavior under every mod, server,
lag condition, or terrain change. The stop reasons and return of control are
part of the behavior, not confirmation that the goal was reached.

## Development and verification

See the [Baritone implementation comparison](BARITONE_COMPARISON.md) for the
terrain-classification bug found in the saved world, the targeted correction,
and the remaining differences in movement execution.

### Source files

| File | Responsibility |
| --- | --- |
| [travel.py](../travel.py) | Game-side collision snapshots, local pathfinding, body-width corridors, walking/swimming/steps, tick steering and movement-distance guard, and expiry timer. |
| [travel_elytra.py](../travel_elytra.py) | Rocket checks, launch, rocket-saving cruise, landing-surface selection, motion prediction, and the walking handoff. |
| [travel_common.py](../travel_common.py) | Coordinate parsing, hunger/flight state readers, food selection, shared stop checks, and input cleanup. |
| [tests/test_travel.py](../tests/test_travel.py) | Offline behavior, geometry, movement-model, inventory, and cleanup tests. |
| [tests/test_java_bridge.py](../tests/test_java_bridge.py) | Optional checks using the installed Pyjinn interpreter and Java API fixtures. |

### Running tests

From the repository directory, with pytest installed:

```text
python -m pytest -q
```

For coverage, pytest-cov is also required:

```text
python -m pytest --cov=travel --cov=travel_common --cov=travel_elytra
```

Players do not need these test packages to run the Minecraft commands.

### Real Pyjinn checks

The optional Java tests execute the shipped surface/collision lookups and walking controller
through the real Pyjinn interpreter. They use Java fixtures, not a running game.
They check numeric argument types, negative/world-border coordinates, unloaded
chunks, flat floor shapes, changed collision states, stale worlds/timers, tick
steering, distance exhaustion, menu cancellation, and delayed movement requests.

Set `MINESCRIPT_TEST_CLASSPATH` to the Pyjinn and Gson JARs, joined with the
platform's classpath separator (`;` on Windows). The installed mod contains
`META-INF/jars/pyjinn-lib-0.14-all.jar` inside its JAR archive; Gson is available
in the launcher's `libraries/com/google/code/gson/gson/` directory. Use local
paths matching your installation. Optionally set `MINESCRIPT_TEST_JAVA` to the
JDK's `java` executable; otherwise the test looks for `java` on PATH.

Then run `python -m pytest -q` again. Without the classpath setting, these Java
tests are skipped. No game connection is made by the test fixtures.

### What verification establishes

The checks cover coordinate handling, arbitrary travel bearings, body-width
detours around independently modeled walls/holes, movement inertia in a
simplified model, single elevation steps, swimming/food transitions, bounded
movement, flight-model approaches, and cleanup.

They do not reproduce the entire Minecraft client/server simulation or every
modded collision shape. Live trials on the intended terrain are still needed
after movement changes; passing tests are not a universal route guarantee.
