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

## Expanded MIT community library

The complete per-file source, pinned commit, SHA-256, runtime, and any local
repair are recorded in [catalog.json](catalog.json). The following packages
retain their original MIT notices. Support modules are counted separately.

| Package | Source revision | MIT notice |
| --- | --- | --- |
| official | [874536fe0a65](https://github.com/maxuser0/minescript-scripts/tree/874536fe0a65068721559b56eaab8d652ce449ba) | [community/official/LICENSE](community/official/LICENSE) |
| official-extras | [f487903ff47c](https://github.com/SmartBoty/Minescript/tree/f487903ff47c4070fe1da4317b72af75d1bf7794) | [community/official-extras/LICENSE](community/official-extras/LICENSE) |
| razrcraft | [7f74c3861cbf](https://github.com/R4z0rX/minescript-scripts/tree/7f74c3861cbf53c36c8acb12c9f3bad7e90dec75) | [community/razrcraft/LICENSE](community/razrcraft/LICENSE) |
| julian | [384f065a5a3c](https://github.com/JulianIsLost/minescript-scripts/tree/384f065a5a3c4c8bfb9dd6494520c2b85eb81625) | [community/julian/LICENSE](community/julian/LICENSE) |
| smooth-mining | [cba6e2722b64](https://github.com/Minescript-Snippets/Macroes/tree/cba6e2722b64b37654f30529c96b1396a58779fe) | [community/smooth-mining/LICENSE](community/smooth-mining/LICENSE) |
| pattern-farming | [0c01b299d09e](https://github.com/Twilight-Lab/Minescript-Macroes/tree/0c01b299d09e2b82522c437fde232348bc4a7bb2) | [community/pattern-farming/LICENSE](community/pattern-farming/LICENSE) |
| skyblock | [a1c79fe3b830](https://github.com/cantaloupasta/Minescript/tree/a1c79fe3b83054f0dafcc4a01e996f6d2d0356cf) | [community/skyblock/LICENSE](community/skyblock/LICENSE) |
| camera | [5373853ef51c](https://github.com/joelkoen/minescript-camera/tree/5373853ef51cfedc7b72a68cafb58aa71005bf17) | [community/camera/LICENSE](community/camera/LICENSE) |
| minekit | [dbf9fd11ccb5](https://github.com/hakenshi/minekit/tree/dbf9fd11ccb542f82afefee98e411f03e74c4f2a) | [community/minekit/LICENSE](community/minekit/LICENSE) |
| pathfinding | [9ab9b73b5e74](https://github.com/n-aoH/Minescript-Pathfinder/tree/9ab9b73b5e744a00fd41cab10e2efdd59af4900f) | [community/pathfinding/LICENSE](community/pathfinding/LICENSE) |
| theta-star | [05f8b8446d8f](https://github.com/hyshenn/thetaSTAR/tree/05f8b8446d8f1181c08518c5813117e0035f7c7e) | [community/theta-star/LICENSE](community/theta-star/LICENSE) |
| tutorials | [f1ff8518c907](https://github.com/sam-ple/minescript-sample/tree/f1ff8518c907ffc91144184768e0b8f3563f585c) | [examples/tutorials/LICENSE](examples/tutorials/LICENSE) |

Four imported programs received limited repairs: the block-image exporter now
imports `echo` before its missing-dependency message, and the advanced farmer
defines its missing `print_help` function. The two A-star examples now stop
their own script instead of killing hardcoded job 1. Their unmodified originals are in
`upstream/curated/` and their original hashes are recorded in the manifest.

`stripmine.py`, `branchmine.py`, the catalog launcher, and the new maintained
utility commands are original MIT additions. They were not copied from the
unlicensed strip-mining script found during discovery.
