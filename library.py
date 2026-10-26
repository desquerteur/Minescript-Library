# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Minescript-Library contributors
"""Search and launch the catalog: \\library list|info|run [ID_OR_FILTER] [ARGS]."""

import hashlib
import json
import runpy
import sys
from pathlib import Path

import minescript as m

from automation_common import run

ROOT = Path(__file__).resolve().parent


def load_catalog():
    return json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))


def script_path(entry):
    path = (ROOT / entry["path"]).resolve()
    if not path.is_relative_to(ROOT) or path.suffix not in {".py", ".pyj"}:
        raise ValueError("Invalid catalog path.")
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise ValueError("Script changed since catalog verification. Rebuild the catalog first.")
    return path


def find_entry(entries, wanted):
    exact = [entry for entry in entries if entry["id"] == wanted]
    if exact:
        return exact[0]
    matches = [entry for entry in entries if entry["name"] == wanted]
    if len(matches) != 1:
        raise ValueError("Use a full catalog ID; the name is missing or ambiguous.")
    return matches[0]


def launch(entry, args):
    if entry["kind"] == "support":
        raise ValueError("This entry is a support module, not a standalone script.")
    path = script_path(entry)
    m.echo(f"Launching {entry['id']}. Status: {entry['status']}")
    if entry["notes"]:
        m.echo("Notes:", "; ".join(entry["notes"]))
    if entry["runtime"] == "Pyjinn":
        command = ROOT.name + "/" + path.relative_to(ROOT).with_suffix("").as_posix()
        m.execute("\\" + " ".join(json.dumps(value) for value in [command, *args]))
        return
    package_root = ROOT / "community" / entry["package"]
    directories = {ROOT, path.parent}
    if package_root.is_dir():
        directories.add(package_root)
        directories.update(file.parent for file in package_root.rglob("*.py"))
    old_path, old_argv = sys.path[:], sys.argv[:]
    try:
        sys.path[:0] = [str(directory) for directory in sorted(directories)]
        sys.argv = [str(path), *args]
        runpy.run_path(str(path), run_name="__main__")
    finally:
        sys.path[:], sys.argv[:] = old_path, old_argv


def main(args):
    entries = load_catalog()["entries"]
    action = args[0] if args else "list"
    if action == "list":
        query = " ".join(args[1:]).casefold()
        matches = [
            entry
            for entry in entries
            if entry["kind"] != "support"
            and query in (entry["id"] + " " + entry["description"]).casefold()
        ]
        for entry in matches[:30]:
            m.echo(f"{entry['id']} — {entry['description']}")
        m.echo(f"{len(matches)} matches; showing up to 30. Narrow the search or open README.md.")
        m.echo("Details: \\library info ID | Launch explicitly: \\library run ID [ARGS]")
        return
    if action not in {"info", "run"} or len(args) < 2:
        raise ValueError("Usage: \\library list [FILTER] | info ID | run ID [ARGS]")
    entry = find_entry(entries, args[1])
    if action == "run":
        launch(entry, args[2:])
        return
    m.echo(entry["description"])
    m.echo(f"Runtime: {entry['runtime']}; kind: {entry['kind']}; status: {entry['status']}")
    m.echo("File:", entry["path"])
    m.echo("Source:", entry["source"])
    m.echo("Notes:", "; ".join(entry["notes"]) or "See source README for arguments and setup.")


if __name__ == "__main__":
    run(main, sys.argv[1:])
