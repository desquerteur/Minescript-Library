# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Refresh maintained entries, file hashes, and the README script catalog."""

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
MAINTAINED = {
    "automine": ("Mine matching visible blocks while staying in place.", "cobblestone"),
    "farm": ("Continuously harvest and replant ripe wheat, carrots, potatoes, and beetroot.", ""),
    "shear": ("Continuously shear reachable sheep while holding shears.", ""),
    "autofish": (
        "Fish continuously and recover from missed casts, lost bobbers, and stalled bites.",
        "",
    ),
    "inventory": ("Count matching carried items and show available inventory slots.", "wheat"),
    "nearby": ("Locate nearby loaded animals, players, and dropped items.", "16 sheep"),
    "entityinfo": ("Inspect the entity in your crosshair, including available health.", "6"),
    "diagnose": ("Display Minecraft, Minescript, Python, and loader versions.", ""),
    "stripmine": (
        "Strip mining: continuously dig and walk a one-wide, two-high tunnel. Optional limits.",
        "",
    ),
    "branchmine": (
        "Branch mining: continuously extend a main tunnel with paired side branches.",
        "",
    ),
    "chunkcoords": ("Show your current chunk and within-chunk coordinates.", ""),
    "bearing": ("Calculate distance and aiming angles to an XYZ coordinate.", "0 64 0"),
    "regioncount": (
        "Count block types in a bounded selection without modifying it.",
        "0 60 0 8 64 8",
    ),
    "orescan": ("Locate ore and ancient debris in nearby loaded client block data.", "4"),
    "cropstatus": ("Count ripe and still-growing crops near you.", "4"),
    "branchplan": ("Preview branch-tunnel endpoint coordinates without digging.", "16 4 6"),
    "worldclock": ("Display the in-game clock, dimension, and weather.", ""),
    "blockwatch": ("Continuously report changes to the initially targeted block.", ""),
    "pickupwatch": ("Continuously report item pickups by your own player.", ""),
    "inventorywatch": ("Continuously report increases and decreases in carried item counts.", ""),
    "equip": ("Find an item in carried storage and select it in the hotbar.", "iron_pickaxe"),
    "library": ("Search, inspect, and explicitly launch entries in this catalog.", "list mining"),
}


def main():
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    catalog["entries"] = [entry for entry in catalog["entries"] if entry["package"] != "maintained"]
    for name, (description, args) in MAINTAINED.items():
        catalog["entries"].append(
            {
                "id": name,
                "name": name,
                "path": name + ".py",
                "package": "maintained",
                "kind": "command",
                "description": description,
                "license": "MIT",
                "source": "https://github.com/desquerteur/Minescript-Library/blob/main/"
                + name
                + ".py",
                "revision": "maintained locally",
                "runtime": "Python",
                "status": "maintained / offline checked / live test pending",
                "notes": [],
                "example": "\\" + name + (" " + args if args else ""),
            }
        )
    for name in ("automation_common", "library_tools"):
        catalog["entries"].append(
            {
                "id": name,
                "name": name,
                "path": name + ".py",
                "package": "maintained",
                "kind": "support",
                "description": "Shared library helper; import rather than launch.",
                "license": "MIT",
                "source": "https://github.com/desquerteur/Minescript-Library/blob/main/"
                + name
                + ".py",
                "revision": "maintained locally",
                "runtime": "Python",
                "status": "support module",
                "notes": [],
            }
        )
    for entry in catalog["entries"]:
        path = (ROOT / entry["path"]).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Catalog path leaves repository")
        content = path.read_bytes()
        ast.parse(content.decode("utf-8-sig"), filename=entry["path"])
        entry["sha256"] = hashlib.sha256(content).hexdigest()
    counts = Counter(entry["kind"] for entry in catalog["entries"])
    catalog["counts"] = dict(counts)
    catalog["counts"]["programs"] = counts["command"] + counts["example"]
    (ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    lines = []
    for heading, kinds in (
        ("Maintained commands", {"command"}),
        ("Community commands and examples", {"command", "example"}),
        ("Support modules — excluded from the program count", {"support"}),
    ):
        lines.extend(
            [
                "### " + heading,
                "",
                "| ID / file | What it does | Runtime and status |",
                "| --- | --- | --- |",
            ]
        )
        for entry in catalog["entries"]:
            maintained = entry["package"] == "maintained"
            if entry["kind"] not in kinds:
                continue
            if heading == "Maintained commands" and not maintained:
                continue
            if heading == "Community commands and examples" and maintained:
                continue
            path = quote(entry["path"], safe="/")
            label = Path(entry["path"]).name if maintained else entry["id"]
            description = entry["description"].replace("|", "\\|")
            if entry.get("example"):
                description += " Example: `" + entry["example"] + "`."
            lines.append(
                f"| [{label}]({path}) | {description} | {entry['runtime']}; {entry['status']} |"
            )
        lines.append("")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    start, end = "<!-- CATALOG START -->", "<!-- CATALOG END -->"
    readme = readme.split(start)[0] + start + "\n\n" + "\n".join(lines) + end + "\n"
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(catalog["counts"]))


if __name__ == "__main__":
    main()
