"""Local Minecraft catalog discovery with vendored fallbacks."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from zipfile import ZipFile

from ..generated import block_catalog as _fallback_block_catalog
from ..generated import entity_catalog as _fallback_entity_catalog
from ..generated import item_catalog as _fallback_item_catalog

_TECHNICAL_BLOCKS = {
    "minecraft:air",
    "minecraft:cave_air",
    "minecraft:void_air",
    "minecraft:water",
    "minecraft:lava",
    "minecraft:bubble_column",
    "minecraft:barrier",
    "minecraft:light",
    "minecraft:structure_void",
    "minecraft:jigsaw",
    "minecraft:command_block",
    "minecraft:chain_command_block",
    "minecraft:repeating_command_block",
    "minecraft:moving_piston",
    "minecraft:piston_head",
    "minecraft:end_gateway",
    "minecraft:end_portal",
    "minecraft:fire",
    "minecraft:soul_fire",
    "minecraft:tripwire",
}


def _constants_from_class(cls) -> tuple[str, ...]:
    return tuple(
        value
        for name, value in cls.__dict__.items()
        if name.isupper() and isinstance(value, str)
    )


FALLBACK_ALL_BLOCKS = _constants_from_class(_fallback_block_catalog.Blocks)
FALLBACK_PLAYER_ITEM_BLOCKS = _constants_from_class(
    getattr(_fallback_block_catalog, "PlayerItemBlocks", _fallback_block_catalog.Blocks)
)
FALLBACK_TECHNICAL_BLOCKS = _constants_from_class(
    getattr(_fallback_block_catalog, "TechnicalBlocks", _fallback_block_catalog.Blocks)
)
FALLBACK_ALL_ENTITIES = _constants_from_class(_fallback_entity_catalog.Entities)
FALLBACK_ALL_ITEMS = _constants_from_class(_fallback_item_catalog.Items)


def _iter_install_roots() -> list[Path]:
    here = Path(__file__).resolve()
    roots = []
    for parent in here.parents:
        if (parent / ".fabric").exists() or (parent / "versions").exists():
            roots.append(parent)
    return roots


def _candidate_jars(root: Path) -> list[Path]:
    candidates: list[Path] = []

    remapped = root / ".fabric" / "remappedJars"
    if remapped.exists():
        candidates.extend(sorted(remapped.glob("**/client-intermediary.jar")))
        candidates.extend(sorted(remapped.glob("**/client*.jar")))

    versions = root / "versions"
    if versions.exists():
        candidates.extend(sorted(versions.glob("*/*.jar")))

    # Keep order stable while deduplicating.
    seen: set[Path] = set()
    result = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen and candidate.is_file():
            seen.add(resolved)
            result.append(candidate)
    return result


def _load_blocks_from_jar(jar_path: Path):
    with ZipFile(jar_path) as jar:
        blockstates = sorted(
            {
                "minecraft:" + Path(entry.filename).stem
                for entry in jar.infolist()
                if entry.filename.startswith("assets/minecraft/blockstates/")
                and entry.filename.endswith(".json")
            }
        )
        items = {
            "minecraft:" + Path(entry.filename).stem
            for entry in jar.infolist()
            if entry.filename.startswith("assets/minecraft/items/")
            and entry.filename.endswith(".json")
        }

    if not blockstates:
        raise ValueError(f"No blockstates found in jar: {jar_path}")

    player_item_blocks = tuple(block_id for block_id in blockstates if block_id in items)
    technical_blocks = tuple(block_id for block_id in blockstates if block_id in _TECHNICAL_BLOCKS)
    return tuple(blockstates), player_item_blocks, technical_blocks, str(jar_path)


@lru_cache(maxsize=1)
def load_block_catalog():
    for root in _iter_install_roots():
        for jar_path in _candidate_jars(root):
            try:
                return _load_blocks_from_jar(jar_path)
            except Exception:
                continue

    return (
        FALLBACK_ALL_BLOCKS,
        FALLBACK_PLAYER_ITEM_BLOCKS,
        FALLBACK_TECHNICAL_BLOCKS,
        "vendored-fallback",
    )


def _load_items_from_jar(jar_path: Path):
    with ZipFile(jar_path) as jar:
        items = sorted(
            {
                "minecraft:" + Path(entry.filename).stem
                for entry in jar.infolist()
                if entry.filename.startswith("assets/minecraft/items/")
                and entry.filename.endswith(".json")
            }
        )

    if not items:
        raise ValueError(f"No items found in jar: {jar_path}")

    return tuple(items), str(jar_path)


def _load_entities_from_jar(jar_path: Path):
    with ZipFile(jar_path) as jar:
        raw_lang = jar.read("assets/minecraft/lang/en_us.json")
        lang = json.loads(raw_lang)
        entities = sorted(
            {
                "minecraft:" + key.split("entity.minecraft.", 1)[1]
                for key in lang
                if key.startswith("entity.minecraft.")
                and "." not in key.split("entity.minecraft.", 1)[1]
            }
        )

    if not entities:
        raise ValueError(f"No entities found in jar: {jar_path}")

    return tuple(entities), str(jar_path)


@lru_cache(maxsize=1)
def load_item_catalog():
    for root in _iter_install_roots():
        for jar_path in _candidate_jars(root):
            try:
                return _load_items_from_jar(jar_path)
            except Exception:
                continue

    return FALLBACK_ALL_ITEMS, "vendored-fallback"


@lru_cache(maxsize=1)
def load_entity_catalog():
    for root in _iter_install_roots():
        for jar_path in _candidate_jars(root):
            try:
                return _load_entities_from_jar(jar_path)
            except Exception:
                continue

    return FALLBACK_ALL_ENTITIES, "vendored-fallback"
