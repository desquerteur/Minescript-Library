# Sources and licenses

All executable scripts in this library are MIT-licensed. The Minescript mod
is a separate prerequisite; its files are not copied into this repository.

## Adapted community scripts

### Automatic fishing

- Author: Thehatmans, copyright 2026.
- Source: [MsAutoFishing](https://github.com/Thehatmans/MsAutoFishing).
- Pinned revision: `2832c62423000e90d4cf49f586928d7dada1d5c5`.
- Original file: [AutoFishing.py](https://github.com/Thehatmans/MsAutoFishing/blob/2832c62423000e90d4cf49f586928d7dada1d5c5/AutoFishing.py).
- Unchanged snapshot: `upstream/AutoFishing.py.txt`.
- Snapshot SHA-256: `3f9f25083791ea57681417f0a4f999c4c3fe4e16dc6e04411c617eb5a58fd394`.
- Original full license: [licenses/MsAutoFishing-MIT.txt](licenses/MsAutoFishing-MIT.txt).
- Installed adaptation: `autofish.py`.
- Changes: standard Minescript import, finite polling, input cleanup, stop
  controls, settling before bite detection, and binding a newly cast bobber.
  Removed the server-specific `/sellall` command and broken armor-stand check.

### Sheep shearing

- Author: Alex Phommarath, copyright 2026.
- Source: [Scripts-For-MCSMP](https://github.com/LaosyAlex/Scripts-For-MCSMP).
- Pinned revision: `8725efe812bf55aa29deb8a63ea4ad18e124c5a3`.
- Original file: [shearsheep.py](https://github.com/LaosyAlex/Scripts-For-MCSMP/blob/8725efe812bf55aa29deb8a63ea4ad18e124c5a3/shearsheep.py).
- Unchanged snapshot: `upstream/shearsheep.py.txt`.
- Snapshot SHA-256: `8db8f6d45d2d21dc923d180f9bb45ecd0c67d113f1ad9723319510f8f0cf9c61`.
- Original full license: [licenses/Scripts-For-MCSMP-MIT.txt](licenses/Scripts-For-MCSMP-MIT.txt).
- Installed adaptation: `shear.py`.
- Changes: removed machine-specific log paths, chest coordinates, automatic
  walking, Windows sound calls, and the missing Minescript Plus dependency.
  Uses visible sheep within reach, cooldowns, and the held shears. No chest storage.

### Inventory counts, nearby entities, and targeted entity information

- Author: Alex Phommarath, copyright 2026.
- Source: [Scripts-For-MCSMP](https://github.com/LaosyAlex/Scripts-For-MCSMP),
  pinned revision `8725efe812bf55aa29deb8a63ea4ad18e124c5a3`.
- Original full license: [licenses/Scripts-For-MCSMP-MIT.txt](licenses/Scripts-For-MCSMP-MIT.txt).
- Original files and installed adaptations:

| Original source | Installed script | Preserved snapshot | Snapshot SHA-256 |
| --- | --- | --- | --- |
| [logPlayerInventory.py](https://github.com/LaosyAlex/Scripts-For-MCSMP/blob/8725efe812bf55aa29deb8a63ea4ad18e124c5a3/logPlayerInventory.py) | `inventory.py` | `upstream/logPlayerInventory.py.txt` | `2b836d1e24d0dcdf6b9dc655f79cfcbec97b88ef37e5b86bba7880d9dcf23b9e` |
| [logAllEntities.py](https://github.com/LaosyAlex/Scripts-For-MCSMP/blob/8725efe812bf55aa29deb8a63ea4ad18e124c5a3/logAllEntities.py) | `nearby.py` | `upstream/logAllEntities.py.txt` | `b9da2b4de0db894406d5dcd0d516777c7caf3fa01e85da249b9800556120c264` |
| [getEntityInfo.py](https://github.com/LaosyAlex/Scripts-For-MCSMP/blob/8725efe812bf55aa29deb8a63ea4ad18e124c5a3/getEntityInfo.py) | `entityinfo.py` | `upstream/getEntityInfo.py.txt` | `f93fd3c7818e77bbf8646a715d3bd73a75fdd771d046d238816bbbb787a39303` |

Changes: removed hardcoded log paths and the unused Minescript Plus import.
Output goes to local chat. Added item totals, filtering, distance limits,
a cap on displayed entities, and handling for an empty crosshair target.
NBT dumps are omitted from the targeted-entity summary.

### Version diagnostics

- Author: RazrCraft, copyright 2026.
- Source: [Minescripters/Diag](https://github.com/Minescripters/Diag).
- Pinned revision: `9be7601fba94fd85cbe19e1c7bf739dcf496c9d6`.
- Original file: [diag.pyj](https://github.com/Minescripters/Diag/blob/9be7601fba94fd85cbe19e1c7bf739dcf496c9d6/diag.pyj).
- Unchanged snapshot: `upstream/diag.pyj.txt`.
- Snapshot SHA-256: `28e3e7af73c4787b53c702a5f3c010f9ff91531f72ee090de60dc8a9ac9e8ac9`.
- Original full license: [licenses/Diag-MIT.txt](licenses/Diag-MIT.txt).
- Installed adaptation: `diagnose.py`.
- Changes: replaced Java/Pyjinn reflection with the public Python
  `version_info()` API. Simplified the report to local chat, removed file
  writes and configuration dumps, and removed nested command execution.

## Original additions

`automine.py`, `farm.py`, `automation_common.py`, and the regression tests were
added for this collection and are covered by the root [MIT license](LICENSE).
They are not represented as unmodified downloads from another author.
