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

## Original additions

`automine.py`, `farm.py`, `automation_common.py`, and the regression tests were
added for this collection and are covered by the root [MIT license](LICENSE).
They are not represented as unmodified downloads from another author.
