# Minekit

Small, vendorable DX layer for Minescript.
The goal is to have a no build library that abstracts the implementation of minescript, improving DX experience and making it easier to make scripts using minescript.
To use it, all you need to do is clone this repository into your minescript folder and use it.

## Layout

```text
minekit/
  control/
  game/
  internal/
  generated/
commands/
tools/
README.md
LICENSE
```

- `minekit/` is the library.
- `minekit/control/` contains player/input controllers.
- `minekit/game/` contains world-facing helpers such as angles, blocks and commands.
- `minekit/internal/` contains private implementation details.
- `minekit/generated/` contains vendored catalog snapshots.
- `commands/` contains ready-to-copy reference scripts built on top of `minekit`.
- `tools/` contains maintenance scripts such as catalog generation.

## Requirements

- Python standard library
- `minescript` available in the current project environment

This library does not try to install or configure Minescript for you. It only wraps the raw API with a smaller, more ergonomic layer.

## Quick Start

Copy or clone this repository into a Minescript scripts folder, then import from `minekit`:

```python
from minekit.control.player import PlayerController
from minekit.control.inventory import InventoryController
from minekit.control.hotkeys import HotkeyController
from minekit.control.logs import LogController
from minekit.const import Action, Direction, HotbarSlot, KeyCode
from minekit.game.angles import PITCH_BLOCK_FACE

player = PlayerController()
inventory = InventoryController()
log = LogController(tag="miner")
player.look(direction=Direction.NORTH, pitch=PITCH_BLOCK_FACE)
player.look_at_block((10, 64, -3), smooth=True)
inventory.select(HotbarSlot.SLOT_1)
player.spam_key(Action.USE, count=8)
log.info("Script loaded")

current_item = inventory.current_item()
if current_item and current_item.name == "minecraft:diamond_pickaxe":
    log.info(current_item.durability)

rotten_flesh_count = inventory.aggregate_items("minecraft:rotten_flesh")
all_items = inventory.aggregate_items()

with HotkeyController() as hotkeys:
    running = False
    while True:
        running = hotkeys.toggle_on_press(KeyCode.F8, running, timeout=0.05)
```

## Modules

### `minekit.control.player`

High-level player controller:

- `snapshot()`
- `position()`
- `orientation()`
- `look(...)`
- `look_at_block(...)`
- `step(...)`
- `tap(...)`
- `spam_key(...)`
- `center_on_block(...)`

### `minekit.control.inventory`

Inventory and hotbar helpers:

- `items()`
- `hand_items()`
- `current_item()`
- `current_offhand_item()`
- `selected_slot()`
- `select(...)`
- `find_first(...)`
- `select_first(...)`
- `aggregate_items(...)`
- `total_count(...)`
- `item_nbt(...)`
- `current_item_nbt()`
- `current_offhand_item_nbt()`
- `current_item_is_usable(...)`
- `current_offhand_item_is_usable(...)`

### `minekit.control.mouse`

Mouse helpers mapped to Minecraft actions:

- `down(...)`
- `up(...)`
- `click(...)`
- `spam(...)`
- `left_click(...)`
- `right_click(...)`
- `middle_click(...)`

### `minekit.control.keyboard`

Keyboard helpers mapped to `press_key_bind(...)`:

- `down(...)`
- `up(...)`
- `tap(...)`
- `spam(...)`

### `minekit.control.hotkeys`

Keyboard event polling and toggle helpers:

- `poll(...)`
- `is_press(...)`
- `is_release(...)`
- `is_repeat(...)`
- `wait_for_press(...)`
- `toggle_on_press(...)`

### `minekit.control.logs`

Local-only chat logging helpers:

- `log(...)`
- `info(...)`
- `warn(...)`
- `error(...)`
- `debug(...)`
- `exception(...)`
- `traceback(...)`

### `minekit.game.angles`

Yaw/pitch constants and helpers:

- `YAW_NORTH`, `YAW_SOUTH`, `YAW_EAST`, `YAW_WEST`
- `PITCH_LEVEL`, `PITCH_BLOCK_FACE`, `PITCH_DOWN`
- `yaw_for(...)`
- `normalize_yaw(...)`
- `clamp_pitch(...)`
- `yaw_pitch_to_block(...)`

### `minekit.game.blocks`

Helpers for block ids and block states:

- `block_name(...)`
- `split_block_state(...)`
- `with_block_states(...)`
- `is_unloaded_block(...)`

### `minekit.const`

Public constants facade:

- `Blocks`
- `Entities`
- `Items`
- `Direction`
- `Action`
- `HotbarSlot`
- `KeyBind`
- `KeyCode`
- `MouseButton`
- `EntitySort`

### `minekit.game.commands`

Command builders on top of `minescript.execute(...)`:

- `run(...)`
- `set_block(...)`
- `fill(...)`
- `merge_block_data(...)`
- `sign_nbt(...)`

## Reference Scripts

The `commands/` folder contains small ready-to-copy scripts:

- `commands/look_at_block.py`
- `commands/spam_key.py`

They import the local `minekit` package directly and do not rely on anything beyond Python + Minescript.

## Catalogs

Block, item and entity catalogs are committed in `minekit/generated/` as plain constant classes. They are regenerated from the local Minecraft installation and meant to be versioned in Git.

To regenerate those catalogs from the current installation:

```bash
python tools/generate_catalogs.py
```

## Design Rules

- Zero config for basic use
- Zero dependencies outside Python stdlib and Minescript
- Thin wrappers over raw Minescript calls
- Keep the API small and readable
- Prefer semantic names over magic strings and magic numbers
