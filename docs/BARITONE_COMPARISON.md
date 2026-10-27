# Walking: Baritone and this implementation

Review date: 2026-10-26. Reference: Baritone's `1.21.4` branch at
[`c55a9c5`](https://github.com/cabaletta/baritone/tree/c55a9c5d9a333c9f0336179a96c13a178fcbc2d4).
This is an architecture comparison, not a claim that that Baritone build runs
on Minecraft 26.3.

**Historical review:** the table describes the implementation reviewed on that
date. The subsequent [walking update](TRAVEL.md#game-tick-walking-control) adds
live collision-shape snapshots, game-tick steering/distance checks, and a pause
before eating. Python still plans routes and coordinates steps/swimming;
the complete native movement-state architecture proposed below is not delivered.

## What differs

| Concern | Baritone reference | Our walking script |
| --- | --- | --- |
| Terrain recognition | Queries Minecraft pathfinding/collision properties, with special rules for hazards, fluids, doors, and other block types. | `passable()` and `support()` classify block names and a limited set of states. An omitted non-colliding plant can wrongly stop an otherwise valid route. |
| Executing a route | `PathExecutor` advances through movement objects, checks their status and changing costs, and consults whether cancellation is safe. | `Walker.follow()` mixes flat-corridor execution with separate step/swimming routines and a generic three-failure stop. It has less information about why an action failed. |
| Movement timing | Movement and input handlers participate in game ticks; traversal and elevation changes have dedicated implementations. | Planning and steering mostly run through Python bridge calls. A game-side movement lease holds forward and bounds how long it remains pressed, but is not a full movement executor. |
| Verification | The implementation contains many block- and action-specific rules. | Our simplified simulation tests geometry, timing, and cleanup but does not reproduce Minecraft's complete collision or movement rules. Passing it cannot establish live terrain compatibility. |

Primary sources:
[MovementHelper](https://github.com/cabaletta/baritone/blob/c55a9c5d9a333c9f0336179a96c13a178fcbc2d4/src/main/java/baritone/pathing/movement/MovementHelper.java#L157),
[PathExecutor](https://github.com/cabaletta/baritone/blob/c55a9c5d9a333c9f0336179a96c13a178fcbc2d4/src/main/java/baritone/pathing/path/PathExecutor.java#L189),
[Movement](https://github.com/cabaletta/baritone/blob/c55a9c5d9a333c9f0336179a96c13a178fcbc2d4/src/main/java/baritone/pathing/movement/Movement.java),
[MovementTraverse](https://github.com/cabaletta/baritone/blob/c55a9c5d9a333c9f0336179a96c13a178fcbc2d4/src/main/java/baritone/pathing/movement/movements/MovementTraverse.java),
[InputOverrideHandler](https://github.com/cabaletta/baritone/blob/c55a9c5d9a333c9f0336179a96c13a178fcbc2d4/src/main/java/baritone/utils/InputOverrideHandler.java#L86).
Our implementation is in [travel.py](../travel.py).

We already use A* locally. The immediate problem is that a planner cannot find
or execute a useful path when its terrain model rejects the starting block.
Increasing search distance or holding forward longer does not correct that.

## Reproduced failure and correction

The game log showed rejected starting terrain even after the tick rate returned
to 20. A read-only inspection of a saved player location found a grass-block
floor, `minecraft:leaf_litter` at the feet, and air above it. The installed
Minecraft 26.3 block registration marks leaf litter as non-colliding. Our
recognized-plant list omitted it, so `Terrain.traversable()` rejected that start.

Adding leaf litter to the recognized plants allows the saved terrain to produce
a path. Regression tests cover all four litter amounts, starting on litter,
walking continuously through it, and retaining a stop for hazardous berry bushes.
This establishes one concrete failure cause; it does not establish that every
reported movement failure had the same cause.

Startup and corridor failures now report the rejected block and coordinates
where available. Stalls report the lack of movement. Step diagnostics check
both permitted heights before blaming a cell. This makes the next live failure
inspectable instead of repeating only a generic blocked message.

The saved world and extracted Minecraft/reference files stay outside this
repository. No live game trial was performed by the automated tests.

## Recommended next work

1. Replace name-list collision guesses with a cached reader of the installed
   game's block collision shapes, fluid states, and hazard traits. Test actual
   player-width clearance and support, including partial blocks and unloaded
   chunks. Retain explicit hazard rules; an empty collision shape alone does
   not mean a block is safe.
2. Move continuous movement execution into a game-tick state machine with
   explicit traverse, ascend, descend, and swim states. Keep Python responsible
   for goals and planning. Preserve cancellation, food pauses, and input cleanup.
3. Add repeatable live routes covering litter, slopes, shorelines, corners,
   chunk boundaries, and delayed updates; record action and block reasons.

These are proposed changes, not features delivered by this patch.

Baritone's [source license](https://github.com/cabaletta/baritone/blob/c55a9c5d9a333c9f0336179a96c13a178fcbc2d4/LICENSE)
is LGPL-3.0. It was studied as a reference; no Baritone source was copied into
this MIT library.
