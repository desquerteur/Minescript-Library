# Minescript-Library

A MIT-only library of Minecraft scripts, with **101 command and tutorial program
files**, plus support modules. Every program below has a name, purpose, source,
file hash, and runtime in [catalog.json](catalog.json). Support modules, tests,
upstream reference snapshots, fork duplicates, and incomplete fragments do not
count toward the 101 programs. The library combines 22 maintained commands,
41 community commands/examples, and 38 extracted tutorial examples.

## Start here

Requires your existing Minescript 5.0 installation and Python 3.10+.
Keep this repository in `minescript/Minescript-Library`. Your Windows config
should contain:

```text
command_path=.;Minescript-Library;system/exec
```

The maintained commands can be run by their short names:

```text
\stripmine 16 300
\branchmine 16 4 6 600
\branchplan 16 4 6
\orescan 4
\cropstatus 4
\farm 300
```

For strip mining, stand on solid natural blocks, face the tunnel direction,
and hold a pickaxe. `stripmine` digs a 1-block-wide, 2-block-high tunnel of the
requested length. `branchmine LENGTH SPACING BRANCH [SECONDS]` adds paired
side tunnels at each spacing interval and returns to the main tunnel.
They stop on nearby detected fluids, unsupported floors/materials, falling
ceiling blocks, low health/damage, a changed tool, a full inventory, blocked
movement, or their time limit. Checks cover the immediate next cell and its
neighbors; they cannot guarantee protection against every cave hazard.
They do not place torches, replace tools, or deposit inventory.

**F8** or opening chat/a menu stops maintained timed scripts. Their default
duration is 300 seconds, allowed range 1–3600. `\killjob -1` is the emergency
stop for all Minescript jobs. Run one movement/interaction automation at a time.
Minecraft must remain responsive for script stop controls to work.

## Search the library

```text
\library list mining
\library list farming
\library list camera
\library info stripmine
\library run stripmine 16 300
```

`list` searches IDs and descriptions and shows up to 30 results. Use a full ID
from the tables for ambiguous community names. `info` shows source, runtime,
status, and review notes. `run` checks the recorded file hash before launching;
it never installs Python packages or starts other catalog entries automatically.
Third-party entries keep their filenames and package folders separate. Four small
upstream bugs have documented local fixes with original snapshots preserved.
The Python launcher adds their package folders to the import path.
Pyjinn entries launch as separate Minescript commands.

## What the status means

- **Maintained / offline checked:** supported by local static checks and regression
  tests. In-game trials are still required, including for the new mining scripts.
- **Manual setup / live test pending:** community code preserved from a pinned
  source revision. Read its package README, arguments, hotbar requirements, and
  imports before running. Some target older Minecraft/Minescript versions or
  SkyBlock-specific mechanics and need adaptation for Minecraft 26.3.
- **Tutorial example:** a complete executable teaching example extracted from its
  source tutorial. Some require cheats/operator commands or Minescript Plus.
  A syntax check does not prove its API calls still work on your game version.
- **Support:** reusable modules rather than standalone programs; excluded from
  the 101-program count.

Source notes in the catalog flag network access, dynamic Python execution,
Java reflection, file writes, and player interactions where detected. Community
scripts are not given the maintained scripts' F8 stop behavior automatically.
Creative building, teleportation, summoning, and some examples require command
permissions. The vendor code has not been made uniformly compatible or audited
for every runtime behavior. Nothing is launched while importing this library.
Only MIT-licensed code is bundled; external dependencies with another or an
unknown license are not silently copied in.

## Sources and verification

See [SOURCES.md](SOURCES.md) for original credits and pinned revisions, each
community package's `LICENSE`, and [research/README.md](research/README.md) for
search scope and exclusions. This was a broad public-source search, not a claim
that every webpage on the internet was searched.

Offline tests use a fake Minescript bridge and do not operate Minecraft. Catalog
checks verify hashes, IDs, MIT provenance, syntax, and README coverage. Mining
checks cover fluids, unsupported floors, falling ceilings, entity interference,
route planning, tool changes, and cleanup. Run:

```text
python -m pytest -q
python tools/build_catalog.py
```

The catalog generator refreshes maintained-file hashes after intentional edits.
Python packages are needed only for development checks. Community runtime
requirements are recorded by their imports and upstream documentation.
The current verification result is recorded in [research/VERIFICATION.md](research/VERIFICATION.md).

## Complete script catalog

A searchable local preview is available with `python tools/preview_catalog.py`.
Open `http://127.0.0.1:8765` in your browser. It serves only this catalog and
its preview page on your own computer.

Use `\library info ID` for source and setup details, and
`\library run ID [ARGS]` to launch explicitly.

<!-- CATALOG START -->

### Maintained commands

| ID / file | What it does | Runtime and status |
| --- | --- | --- |
| [automine.py](automine.py) | Mine matching visible blocks while staying in place. Example: `\automine cobblestone 120`. | Python; maintained / offline checked / live test pending |
| [farm.py](farm.py) | Harvest and replant ripe wheat, carrots, potatoes, and beetroot. Example: `\farm 300`. | Python; maintained / offline checked / live test pending |
| [shear.py](shear.py) | Shear reachable sheep while holding shears. Example: `\shear 300`. | Python; maintained / offline checked / live test pending |
| [autofish.py](autofish.py) | Cast, detect bobber dips, reel in, and recast while holding a rod. Example: `\autofish 300`. | Python; maintained / offline checked / live test pending |
| [inventory.py](inventory.py) | Count matching carried items and show available inventory slots. Example: `\inventory wheat`. | Python; maintained / offline checked / live test pending |
| [nearby.py](nearby.py) | Locate nearby loaded animals, players, and dropped items. Example: `\nearby 16 sheep`. | Python; maintained / offline checked / live test pending |
| [entityinfo.py](entityinfo.py) | Inspect the entity in your crosshair, including available health. Example: `\entityinfo 6`. | Python; maintained / offline checked / live test pending |
| [diagnose.py](diagnose.py) | Display Minecraft, Minescript, Python, and loader versions. Example: `\diagnose`. | Python; maintained / offline checked / live test pending |
| [stripmine.py](stripmine.py) | Strip mining: dig and walk a one-wide, two-high tunnel with bounded hazard checks. Example: `\stripmine 16 300`. | Python; maintained / offline checked / live test pending |
| [branchmine.py](branchmine.py) | Branch mining: dig a main tunnel with paired side branches and return to the center. Example: `\branchmine 16 4 6 600`. | Python; maintained / offline checked / live test pending |
| [chunkcoords.py](chunkcoords.py) | Show your current chunk and within-chunk coordinates. Example: `\chunkcoords`. | Python; maintained / offline checked / live test pending |
| [bearing.py](bearing.py) | Calculate distance and aiming angles to an XYZ coordinate. Example: `\bearing 0 64 0`. | Python; maintained / offline checked / live test pending |
| [regioncount.py](regioncount.py) | Count block types in a bounded selection without modifying it. Example: `\regioncount 0 60 0 8 64 8`. | Python; maintained / offline checked / live test pending |
| [orescan.py](orescan.py) | Locate ore and ancient debris in nearby loaded client block data. Example: `\orescan 4`. | Python; maintained / offline checked / live test pending |
| [cropstatus.py](cropstatus.py) | Count ripe and still-growing crops near you. Example: `\cropstatus 4`. | Python; maintained / offline checked / live test pending |
| [branchplan.py](branchplan.py) | Preview branch-tunnel endpoint coordinates without digging. Example: `\branchplan 16 4 6`. | Python; maintained / offline checked / live test pending |
| [worldclock.py](worldclock.py) | Display the in-game clock, dimension, and weather. Example: `\worldclock`. | Python; maintained / offline checked / live test pending |
| [blockwatch.py](blockwatch.py) | Report changes to the block targeted when the script starts. Example: `\blockwatch 300`. | Python; maintained / offline checked / live test pending |
| [pickupwatch.py](pickupwatch.py) | Report item pickups by your own player. Example: `\pickupwatch 300`. | Python; maintained / offline checked / live test pending |
| [inventorywatch.py](inventorywatch.py) | Report increases and decreases in carried item counts. Example: `\inventorywatch 300`. | Python; maintained / offline checked / live test pending |
| [equip.py](equip.py) | Find an item in carried storage and select it in the hotbar. Example: `\equip iron_pickaxe`. | Python; maintained / offline checked / live test pending |
| [library.py](library.py) | Search, inspect, and explicitly launch entries in this catalog. Example: `\library list mining`. | Python; maintained / offline checked / live test pending |

### Community commands and examples

| ID / file | What it does | Runtime and status |
| --- | --- | --- |
| [official-timer-v1-timer](community/official/timer/v1/timer.py) | Schedule or repeat chat messages, local messages, or Minecraft commands. | Python; manual setup / live test pending |
| [official-sphere-v2-sphere](community/official/sphere/v2/sphere.py) | Build a hollow sphere from blocks; requires creative command permissions. | Python; manual setup / live test pending |
| [official-interpreter-v1-interpreter](community/official/interpreter/v1/interpreter.py) | Interactive Python interpreter in Minecraft chat with Java reflection. | Python; manual setup / live test pending |
| [official-image-to-blocks-v1-image-to-blocks](community/official/image_to_blocks/v1/image_to_blocks.py) | Convert a PNG image and optional depth map into Minecraft blocks. | Python; manual setup / live test pending |
| [official-execute-book-v1-execute-book](community/official/execute_book/v1/execute_book.py) | Execute a Python program stored in a written Minecraft book. | Python; manual setup / live test pending |
| [official-eval-v1-eval](community/official/eval/v1/eval.py) | Evaluate Python expressions or statements from Minecraft chat. | Python; manual setup / live test pending |
| [official-blocks-to-image-v1-blocks-to-image](community/official/blocks_to_image/v1/blocks_to_image.py) | Export a top-down block region as a PNG image and depth map. | Python; manual setup / live test pending |
| [official-extras-base-minescript-tools-cylinder](community/official-extras/base%20minescript%20tools/cylinder.py) | Build the lateral surface of a cylinder using Minecraft commands. | Python; manual setup / live test pending |
| [official-extras-base-minescript-tools-draw-text](community/official-extras/base%20minescript%20tools/draw_text.py) | Draw configurable text overlays on the game screen. | Python; manual setup / live test pending |
| [razrcraft-example-config-lib](community/razrcraft/example_config_lib.py) | Demonstrate JSON-backed per-script settings. | Python; manual setup / live test pending |
| [razrcraft-gui](community/razrcraft/gui.py) | Demonstrate an interactive Minescript GUI. | Python; manual setup / live test pending |
| [razrcraft-ls2](community/razrcraft/ls2.py) | Show an enhanced list of available Minescript scripts. | Python; manual setup / live test pending |
| [razrcraft-scanner](community/razrcraft/scanner.py) | Interactively scan blocks and display scan results. | Python; manual setup / live test pending |
| [razrcraft-test-mouse](community/razrcraft/test_mouse.py) | Display mouse event information for debugging controls. | Python; manual setup / live test pending |
| [razrcraft-svc-key-svc](community/razrcraft/svc/key_svc.py) | Run a keyboard event service for script key bindings. | Python; manual setup / live test pending |
| [razrcraft-svc-ms-key-command](community/razrcraft/svc/ms_key_command.py) | Bind Minescript commands to keyboard shortcuts. | Python; manual setup / live test pending |
| [razrcraft-tools-mappings-downloader](community/razrcraft/tools/mappings_downloader.py) | Download Java mappings needed by older Minecraft versions. | Python; manual setup / live test pending |
| [razrcraft-tools-wider-chat](community/razrcraft/tools/wider_chat.pyj) | Adjust Minecraft chat width through Java reflection; uses old field mappings. | Pyjinn; manual setup / live test pending |
| [razrcraft-worldrender-worldrender-test1](community/razrcraft/WorldRender/worldrender_test1.py) | Demonstrate rendering world-space geometry. | Python; manual setup / live test pending |
| [razrcraft-worldrender-worldrender-test2](community/razrcraft/WorldRender/worldrender_test2.py) | Demonstrate a second world-space overlay scene. | Python; manual setup / live test pending |
| [razrcraft-minescript-plus-examples-actionbar-event](community/razrcraft/Minescript-Plus/examples/actionbar_event.py) | Read actionbar events from the game. | Python; manual setup / live test pending |
| [razrcraft-minescript-plus-examples-actionbar-event2](community/razrcraft/Minescript-Plus/examples/actionbar_event2.py) | Alternative actionbar event listener example. | Python; manual setup / live test pending |
| [razrcraft-minescript-plus-examples-press-key](community/razrcraft/Minescript-Plus/examples/press_key.py) | Demonstrate triggering a Minecraft key binding. | Python; manual setup / live test pending |
| [razrcraft-minescript-plus-examples-swap](community/razrcraft/Minescript-Plus/examples/swap.py) | Demonstrate swapping an inventory slot with a hotbar slot. | Python; manual setup / live test pending |
| [razrcraft-minescript-plus-examples-title-actionbar](community/razrcraft/Minescript-Plus/examples/title-actionbar.py) | Display title, subtitle, and actionbar messages. | Python; manual setup / live test pending |
| [razrcraft-minescript-plus-examples-trading](community/razrcraft/Minescript-Plus/examples/trading.py) | Demonstrate a single selected villager trade. | Python; manual setup / live test pending |
| [julian-scripts-astar](community/julian/scripts/astar.pyj) | Calculate and visualize an A-star walking route. | Pyjinn; manual setup / live test pending |
| [julian-scripts-astar-walk](community/julian/scripts/astar_walk.pyj) | Walk a route generated by the A-star example. | Pyjinn; manual setup / live test pending |
| [julian-scripts-blocktp](community/julian/scripts/blocktp.pyj) | Move to a selected block using the source block-teleport interaction. | Pyjinn; manual setup / live test pending |
| [smooth-mining-advanced-autofarmer-hype](community/smooth-mining/Advanced%20Autofarmer%20%28HYPE%29.py) | Run a configurable crop-farming macro with its source hotbar setup. | Python; manual setup / live test pending |
| [smooth-mining-smoothlookautomining](community/smooth-mining/SmoothLookAutoMining.py) | Find configured nearby blocks, rotate smoothly to them, and mine them. | Python; manual setup / live test pending |
| [pattern-farming-patternfarmautomation](community/pattern-farming/PatternFarmAutomation.py) | Automate a configurable sequence of movements across patterned farm rows. | Python; manual setup / live test pending |
| [skyblock-pyjinn-beehive](community/skyblock/Pyjinn/beehive.pyj) | Follow SkyBlock beehive waypoints and interact with hives. | Pyjinn; manual setup / live test pending |
| [skyblock-pyjinn-corleone](community/skyblock/Pyjinn/corleone.pyj) | Automate the source SkyBlock Corleone encounter routine. | Pyjinn; manual setup / live test pending |
| [skyblock-pyjinn-dragon](community/skyblock/Pyjinn/dragon.pyj) | Track and interact with SkyBlock dragon encounters. | Pyjinn; manual setup / live test pending |
| [skyblock-pyjinn-esp](community/skyblock/Pyjinn/esp.pyj) | Display nearby entity overlays with the Pyjinn runtime. | Pyjinn; manual setup / live test pending |
| [skyblock-pyjinn-lava](community/skyblock/Pyjinn/lava.pyj) | Run the source SkyBlock lava-fishing interaction routine. | Pyjinn; manual setup / live test pending |
| [skyblock-python-esp-radar](community/skyblock/Python/esp/radar.py) | Display configurable entity radar using a Tkinter control panel. | Python; manual setup / live test pending |
| [skyblock-python-exp-exp](community/skyblock/Python/exp/exp.py) | Automate the source SkyBlock experimentation-table minigames. | Python; manual setup / live test pending |
| [skyblock-python-fish-fish](community/skyblock/Python/fish/fish.py) | Configurable SkyBlock fishing, including trophy and magma modes. | Python; manual setup / live test pending |
| [camera-camera](community/camera/camera.pyj) | Record and play back a Minecraft camera movement sequence. | Pyjinn; manual setup / live test pending |
| [tutorials-guide02-01-detect-held-items-main-off-hand](examples/tutorials/guide02-01-detect-held-items-main-off-hand.py) | Guide 02: ❷ Detect Held Items (Main/Off Hand) | Python; tutorial example / setup and live test pending |
| [tutorials-guide02-02-off-hand](examples/tutorials/guide02-02-off-hand.py) | Guide 02: Off hand | Python; tutorial example / setup and live test pending |
| [tutorials-guide02-03-detect-left-right-clicks](examples/tutorials/guide02-03-detect-left-right-clicks.py) | Guide 02: ❸ Detect Left & Right Clicks | Python; tutorial example / setup and live test pending |
| [tutorials-guide02-04-detect-key](examples/tutorials/guide02-04-detect-key.py) | Guide 02: ❹ Detect Key | Python; tutorial example / setup and live test pending |
| [tutorials-guide02-06-backhome-script-example](examples/tutorials/guide02-06-backhome-script-example.py) | Guide 02: ❻ Backhome Script Example | Python; tutorial example / setup and live test pending |
| [tutorials-guide02-07-record-current-player-position-block-coordinates](examples/tutorials/guide02-07-record-current-player-position-block-coordinates.py) | Guide 02: Record current player position (block coordinates) | Python; tutorial example / setup and live test pending |
| [tutorials-guide03-01-actionbar-countdown](examples/tutorials/guide03-01-actionbar-countdown.py) | Guide 03: ❶ Actionbar Countdown | Python; tutorial example / setup and live test pending |
| [tutorials-guide03-03-scoreboard-countdown](examples/tutorials/guide03-03-scoreboard-countdown.py) | Guide 03: ❷ Scoreboard Countdown | Python; tutorial example / setup and live test pending |
| [tutorials-guide03-04-mm-ss-format-example](examples/tutorials/guide03-04-mm-ss-format-example.py) | Guide 03: MM:SS Format Example | Python; tutorial example / setup and live test pending |
| [tutorials-guide03-05-bossbar-countdown](examples/tutorials/guide03-05-bossbar-countdown.py) | Guide 03: ❸ Bossbar Countdown | Python; tutorial example / setup and live test pending |
| [tutorials-guide05-01-example-listen-to-chat](examples/tutorials/guide05-01-example-listen-to-chat.py) | Guide 05: ❷ Example: Listen to Chat | Python; tutorial example / setup and live test pending |
| [tutorials-guide05-02-example-simple-chat-commands](examples/tutorials/guide05-02-example-simple-chat-commands.py) | Guide 05: ❸ Example: Simple Chat Commands | Python; tutorial example / setup and live test pending |
| [tutorials-guide05-03-script](examples/tutorials/guide05-03-script.py) | Guide 05: Script | Python; tutorial example / setup and live test pending |
| [tutorials-guide06-01-default-damage-debug-all-events](examples/tutorials/guide06-01-default-damage-debug-all-events.py) | Guide 06: ❶ Default Damage Debug (All Events) | Python; tutorial example / setup and live test pending |
| [tutorials-guide06-02-melee-attacks-only](examples/tutorials/guide06-02-melee-attacks-only.py) | Guide 06: ❷ Melee Attacks Only | Python; tutorial example / setup and live test pending |
| [tutorials-guide06-03-add-projectiles](examples/tutorials/guide06-03-add-projectiles.py) | Guide 06: ❸ Add Projectiles | Python; tutorial example / setup and live test pending |
| [tutorials-guide06-04-remaining-hp-kill-detection](examples/tutorials/guide06-04-remaining-hp-kill-detection.py) | Guide 06: ❹ Remaining HP & Kill Detection | Python; tutorial example / setup and live test pending |
| [tutorials-basic01-02-player-position](examples/tutorials/basic01-02-player-position.py) | Basics 01: player_position() | Python; tutorial example / setup and live test pending |
| [tutorials-basic01-03-execute-command-str](examples/tutorials/basic01-03-execute-command-str.py) | Basics 01: execute(command: str) | Python; tutorial example / setup and live test pending |
| [tutorials-basic01-06-summon-mobs-with-delay](examples/tutorials/basic01-06-summon-mobs-with-delay.py) | Basics 01: Summon Mobs with Delay | Python; tutorial example / setup and live test pending |
| [tutorials-basic01-07-circular-mob-summoning](examples/tutorials/basic01-07-circular-mob-summoning.py) | Basics 01: Circular Mob Summoning | Python; tutorial example / setup and live test pending |
| [tutorials-basic01-08-random-mobs-in-a-circle](examples/tutorials/basic01-08-random-mobs-in-a-circle.py) | Basics 01: Random Mobs in a Circle | Python; tutorial example / setup and live test pending |
| [tutorials-basic02-01-player-press-jump](examples/tutorials/basic02-01-player-press-jump.py) | Basics 02: player.press_jump() | Python; tutorial example / setup and live test pending |
| [tutorials-basic02-02-player-get-targeted-block](examples/tutorials/basic02-02-player-get-targeted-block.py) | Basics 02: player.get_targeted_block() | Python; tutorial example / setup and live test pending |
| [tutorials-basic02-03-player-press-use](examples/tutorials/basic02-03-player-press-use.py) | Basics 02: player.press_use() | Python; tutorial example / setup and live test pending |
| [tutorials-basic02-04-player-inventory](examples/tutorials/basic02-04-player-inventory.py) | Basics 02: player.inventory() | Python; tutorial example / setup and live test pending |
| [tutorials-basic02-05-show-inventory-items](examples/tutorials/basic02-05-show-inventory-items.py) | Basics 02: Show inventory items | Python; tutorial example / setup and live test pending |
| [tutorials-basic02-06-register-chat-listener](examples/tutorials/basic02-06-register-chat-listener.py) | Basics 02: register_chat_listener() | Python; tutorial example / setup and live test pending |
| [tutorials-basic02-07-auto-walk-and-interact](examples/tutorials/basic02-07-auto-walk-and-interact.py) | Basics 02: Auto Walk and Interact | Python; tutorial example / setup and live test pending |
| [tutorials-basic02-08-auto-fishing-system](examples/tutorials/basic02-08-auto-fishing-system.py) | Basics 02: Auto Fishing System | Python; tutorial example / setup and live test pending |
| [tutorials-plus01-01-title-subtitle-display](examples/tutorials/plus01-01-title-subtitle-display.py) | plus01: Title & Subtitle Display | Python; tutorial example / setup and live test pending |
| [tutorials-plus01-02-actionbar-test](examples/tutorials/plus01-02-actionbar-test.py) | plus01: Actionbar Test | Python; tutorial example / setup and live test pending |
| [tutorials-plus01-03-check-for-diamond-in-player-inventory](examples/tutorials/plus01-03-check-for-diamond-in-player-inventory.py) | plus01: Check for Diamond in Player Inventory | Python; tutorial example / setup and live test pending |
| [tutorials-plus01-04-search-for-diamond-in-chest](examples/tutorials/plus01-04-search-for-diamond-in-chest.py) | plus01: Search for Diamond in Chest | Python; tutorial example / setup and live test pending |
| [tutorials-plus01-05-read-text-from-targeted-sign](examples/tutorials/plus01-05-read-text-from-targeted-sign.py) | plus01: Read Text from Targeted Sign | Python; tutorial example / setup and live test pending |
| [tutorials-plus01-06-player-information](examples/tutorials/plus01-06-player-information.py) | plus01: Player Information | Python; tutorial example / setup and live test pending |
| [tutorials-plus01-07-world-information](examples/tutorials/plus01-07-world-information.py) | plus01: World Information | Python; tutorial example / setup and live test pending |
| [tutorials-pyjinn01-07-java-stream-api-with-pyjinn-lambdas](examples/tutorials/pyjinn01-07-java-stream-api-with-pyjinn-lambdas.pyj) | pyjinn01: Java Stream API with Pyjinn Lambdas | Pyjinn; tutorial example / setup and live test pending |

### Support modules — excluded from the program count

| ID / file | What it does | Runtime and status |
| --- | --- | --- |
| [official-lib-java-v1-lib-java](community/official/lib_java/v1/lib_java.py) | Support module for official: lib java | Python; manual setup / live test pending |
| [official-lib-blockpack-parser-v1-lib-blockpack-parser](community/official/lib_blockpack_parser/v1/lib_blockpack_parser.py) | Support module for official: lib blockpack parser | Python; manual setup / live test pending |
| [razrcraft-discord-webhook](community/razrcraft/discord_webhook.py) | Support module for razrcraft: discord webhook | Python; manual setup / live test pending |
| [razrcraft-lib-config-lib](community/razrcraft/lib/config_lib.py) | Support module for razrcraft: config lib | Python; manual setup / live test pending |
| [razrcraft-lib-glfw-keycodes](community/razrcraft/lib/glfw_keycodes.py) | Support module for razrcraft: glfw keycodes | Python; manual setup / live test pending |
| [razrcraft-lib-lib-screen](community/razrcraft/lib/lib_screen.py) | Support module for razrcraft: lib screen | Python; manual setup / live test pending |
| [razrcraft-lib-snbt-parser](community/razrcraft/lib/snbt_parser.py) | Support module for razrcraft: snbt parser | Python; manual setup / live test pending |
| [razrcraft-lib-snbt-reader](community/razrcraft/lib/snbt_reader.py) | Support module for razrcraft: snbt reader | Python; manual setup / live test pending |
| [razrcraft-minescript-plus-minescript-plus](community/razrcraft/Minescript-Plus/minescript_plus.py) | Support module for razrcraft: minescript plus | Python; manual setup / live test pending |
| [razrcraft-worldrender-worldrender](community/razrcraft/WorldRender/worldrender.py) | Support module for razrcraft: worldrender | Python; manual setup / live test pending |
| [julian-libs-lib-astar](community/julian/libs/lib_astar.py) | Support module for julian: lib astar | Python; manual setup / live test pending |
| [julian-lib-inv-lib-inv](community/julian/lib_inv/lib_inv.py) | Support module for julian: lib inv | Python; manual setup / live test pending |
| [julian-lib-ren-lib-ren](community/julian/lib_ren/lib_ren.py) | Support module for julian: lib ren | Python; manual setup / live test pending |
| [julian-tools-itemhelper](community/julian/tools/itemhelper.py) | Support module for julian: itemhelper | Python; manual setup / live test pending |
| [minekit-const](community/minekit/const.py) | Support module for minekit: const | Python; manual setup / live test pending |
| [minekit-init](community/minekit/__init__.py) | Support module for minekit:   init   | Python; manual setup / live test pending |
| [minekit-control-hotkeys](community/minekit/control/hotkeys.py) | Support module for minekit: hotkeys | Python; manual setup / live test pending |
| [minekit-control-inventory](community/minekit/control/inventory.py) | Support module for minekit: inventory | Python; manual setup / live test pending |
| [minekit-control-keyboard](community/minekit/control/keyboard.py) | Support module for minekit: keyboard | Python; manual setup / live test pending |
| [minekit-control-logs](community/minekit/control/logs.py) | Support module for minekit: logs | Python; manual setup / live test pending |
| [minekit-control-mouse](community/minekit/control/mouse.py) | Support module for minekit: mouse | Python; manual setup / live test pending |
| [minekit-control-player](community/minekit/control/player.py) | Support module for minekit: player | Python; manual setup / live test pending |
| [minekit-control-timing](community/minekit/control/timing.py) | Support module for minekit: timing | Python; manual setup / live test pending |
| [minekit-control-init](community/minekit/control/__init__.py) | Support module for minekit:   init   | Python; manual setup / live test pending |
| [minekit-game-angles](community/minekit/game/angles.py) | Support module for minekit: angles | Python; manual setup / live test pending |
| [minekit-game-blocks](community/minekit/game/blocks.py) | Support module for minekit: blocks | Python; manual setup / live test pending |
| [minekit-game-commands](community/minekit/game/commands.py) | Support module for minekit: commands | Python; manual setup / live test pending |
| [minekit-game-timing](community/minekit/game/timing.py) | Support module for minekit: timing | Python; manual setup / live test pending |
| [minekit-game-init](community/minekit/game/__init__.py) | Support module for minekit:   init   | Python; manual setup / live test pending |
| [minekit-generated-block-catalog](community/minekit/generated/block_catalog.py) | Support module for minekit: block catalog | Python; manual setup / live test pending |
| [minekit-generated-entity-catalog](community/minekit/generated/entity_catalog.py) | Support module for minekit: entity catalog | Python; manual setup / live test pending |
| [minekit-generated-item-catalog](community/minekit/generated/item_catalog.py) | Support module for minekit: item catalog | Python; manual setup / live test pending |
| [minekit-generated-init](community/minekit/generated/__init__.py) | Support module for minekit:   init   | Python; manual setup / live test pending |
| [minekit-internal-catalog](community/minekit/internal/catalog.py) | Support module for minekit: catalog | Python; manual setup / live test pending |
| [minekit-internal-enums](community/minekit/internal/enums.py) | Support module for minekit: enums | Python; manual setup / live test pending |
| [minekit-internal-types](community/minekit/internal/types.py) | Support module for minekit: types | Python; manual setup / live test pending |
| [minekit-internal-init](community/minekit/internal/__init__.py) | Support module for minekit:   init   | Python; manual setup / live test pending |
| [pathfinding-pathfinder](community/pathfinding/pathfinder.pyj) | Support module for pathfinding: pathfinder | Pyjinn; manual setup / live test pending |
| [theta-star-thetastar](community/theta-star/ThetaStar.py) | Support module for theta-star: ThetaStar | Python; manual setup / live test pending |
| [automation_common.py](automation_common.py) | Shared library helper; import rather than launch. | Python; support module |
| [library_tools.py](library_tools.py) | Shared library helper; import rather than launch. | Python; support module |
<!-- CATALOG END -->
