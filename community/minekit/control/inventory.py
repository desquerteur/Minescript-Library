"""Inventory wrappers for common hotbar tasks."""

from __future__ import annotations

from collections.abc import Mapping
import re

import minescript

from ..internal.enums import HotbarSlot
from ..internal.types import InventoryAggregate, InventoryItem, ItemDurability


def _normalized_id(value: str) -> str:
    return value if ":" in value else f"minecraft:{value}"


def _slot_index(slot: int | HotbarSlot) -> int:
    return int(slot)


_INT_PATTERNS = {
    "damage": (
        re.compile(
            r'(?:"minecraft:damage"|minecraft:damage|Damage|damage)\s*[:=]\s*(\d+)'),
    ),
    "max_damage": (
        re.compile(
            r'(?:"minecraft:max_damage"|minecraft:max_damage|max_damage|MaxDamage|maxDamage)\s*[:=]\s*(\d+)'
        ),
    ),
}


def _parse_nbt_int(nbt: str | None, key: str) -> int | None:
    if not nbt:
        return None
    for pattern in _INT_PATTERNS[key]:
        match = pattern.search(nbt)
        if match:
            return int(match.group(1))
    return None


def _item_value(item, key: str, default=None):
    if item is None:
        return default
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def _validate_expected_item(item, expected_item: str | None):
    if expected_item is None:
        return item

    expected_item = _normalized_id(expected_item)
    actual_item = _item_value(item, "name")
    if actual_item != expected_item:
        raise ValueError(
            f"Expected held item {expected_item!r}, got {actual_item!r}.")
    return item


def _durability_from_nbt(nbt: str | None) -> ItemDurability | None:
    damage = _parse_nbt_int(nbt, "damage")
    if damage is None:
        return None

    max_damage = _parse_nbt_int(nbt, "max_damage")
    remaining = None if max_damage is None else max(0, max_damage - damage)
    ratio = None if max_damage in (None, 0) else remaining / max_damage
    return ItemDurability(
        damage=damage,
        max_damage=max_damage,
        remaining=remaining,
        ratio=ratio,
    )


def _wrap_item(item) -> InventoryItem | None:
    if item is None:
        return None
    nbt = _item_value(item, "nbt", None)
    slot = _item_value(item, "slot", None)
    return InventoryItem(
        name=_item_value(item, "item", None),
        count=_item_value(item, "count", None),
        nbt=nbt,
        slot=None if slot is None else int(slot),
        selected=_item_value(item, "selected", None),
        durability=_durability_from_nbt(nbt),
    )


class InventoryController:
    """Helpers for reading inventory state and selecting hotbar slots."""

    def items(self):
        """Return typed inventory items reported by Minescript."""
        return [_wrap_item(item) for item in minescript.player_inventory()]

    def aggregate_items(self, item_id: str | None = None):
        """Aggregate inventory stacks by item id.

        Args:
            item_id: Optional item id. When provided, return only the total count
                for that item. When omitted, return a dict of aggregates keyed by
                item id.

        Returns:
            ``int`` when ``item_id`` is provided, otherwise
            ``dict[str, InventoryAggregate]``.
        """
        aggregates: dict[str, list[InventoryItem]] = {}
        for item in self.items():
            if item is None or item.name is None:
                continue
            aggregates.setdefault(item.name, []).append(item)

        if item_id is not None:
            wanted = _normalized_id(item_id)
            return sum(item.count or 0 for item in aggregates.get(wanted, ()))

        result: dict[str, InventoryAggregate] = {}
        for name, stacks in aggregates.items():
            slots = tuple(
                item.slot for item in stacks if item.slot is not None)
            result[name] = InventoryAggregate(
                name=name,
                total_count=sum(item.count or 0 for item in stacks),
                stack_count=len(stacks),
                slots=slots,
                selected=any(bool(item.selected) for item in stacks),
                stacks=tuple(stacks),
            )
        return result

    def total_count(self, item_id: str) -> int:
        """Return the total number of matching items across the inventory."""
        return self.aggregate_items(item_id)

    def hand_items(self):
        """Return the raw main-hand and off-hand container reported by Minescript."""
        return minescript.player_hand_items()

    def _selected_inventory_item(self):
        for item in self.items():
            if _item_value(item, "selected", False):
                return item
        return None

    def current_item(self):
        """Return the typed item currently held in the player's main hand."""
        hands = self.hand_items()
        item = _wrap_item(_item_value(hands, "main_hand"))
        if _item_value(item, "name") is None:
            selected = self._selected_inventory_item()
            if selected is not None:
                item = selected
        return item

    def current_offhand_item(self):
        """Return the typed item currently held in the player's off hand."""
        hands = self.hand_items()
        return _wrap_item(_item_value(hands, "off_hand"))

    def selected_slot(self) -> HotbarSlot | None:
        """Return the currently selected hotbar slot, if one is marked selected."""
        for item in self.items():
            if _item_value(item, "selected", False) and _item_value(item, "slot") is not None:
                slot = int(_item_value(item, "slot"))
                if 0 <= slot <= 8:
                    return HotbarSlot(slot)
        return None

    def select(self, slot: int | HotbarSlot) -> int:
        """Select a hotbar slot by integer index or ``HotbarSlot`` constant."""
        return minescript.player_inventory_select_slot(_slot_index(slot))

    def find_first(self, item_id: str, hotbar_only: bool = False):
        """Find the first inventory entry whose item id matches ``item_id``.

        Args:
            item_id: Item id with or without the ``minecraft:`` namespace.
            hotbar_only: Restrict the search to slots 0 through 8.
        """
        wanted = _normalized_id(item_id)
        for item in self.items():
            slot = _item_value(item, "slot", None)
            if hotbar_only and (slot is None or not 0 <= int(slot) <= 8):
                continue
            if _item_value(item, "name", None) == wanted:
                return item
        return None

    def select_first(self, item_id: str):
        """Select the first matching item and return the chosen hotbar slot."""
        item = self.find_first(item_id)
        if item is None:
            return None

        slot = _item_value(item, "slot", None)
        if slot is None:
            raise ValueError(
                f"Inventory item {item_id!r} has no slot metadata.")

        slot = int(slot)
        if 0 <= slot <= 8:
            self.select(slot)
            return HotbarSlot(slot)

        if hasattr(minescript, "player_inventory_slot_to_hotbar"):
            hotbar_slot = minescript.player_inventory_slot_to_hotbar(slot)
            self.select(hotbar_slot)
            return HotbarSlot(hotbar_slot)

        raise ValueError(
            f"Inventory item {item_id!r} was found in slot {slot}, outside the hotbar."
        )

    def item_damage(self, item=None) -> int | None:
        """Return the current damage value for an item, when present in NBT/components.

        Args:
            item: Item stack to inspect. Defaults to the current main-hand item.
        """
        if item is None:
            item = self.current_item()
        return _parse_nbt_int(_item_value(item, "nbt", None), "damage")

    def item_nbt(self, item=None) -> str | None:
        """Return the raw NBT string for an item, when present."""
        if item is None:
            item = self.current_item()
        return _item_value(item, "nbt", None)

    def current_item_nbt(self) -> str | None:
        """Return the raw NBT string for the item currently held in the main hand."""
        return self.item_nbt(self.current_item())

    def current_offhand_item_nbt(self) -> str | None:
        """Return the raw NBT string for the item currently held in the off hand."""
        return self.item_nbt(self.current_offhand_item())

    def item_max_damage(self, item=None) -> int | None:
        """Return the max durability for an item, when present in NBT/components.

        Args:
            item: Item stack to inspect. Defaults to the current main-hand item.
        """
        if item is None:
            item = self.current_item()
        return _parse_nbt_int(_item_value(item, "nbt", None), "max_damage")

    def item_durability(self, item=None) -> ItemDurability | None:
        """Return parsed durability information for an item.

        Args:
            item: Item stack to inspect. Defaults to the current main-hand item.

        Returns:
            ``ItemDurability`` when a damage value is present, otherwise ``None``.
        """
        if item is None:
            item = self.current_item()
        return _item_value(item, "durability", None)

    def item_is_usable(
        self,
        item=None,
        minimum_remaining: int = 1,
    ) -> bool:
        """Return whether an item has readable durability and enough remaining uses."""
        durability = self.item_durability(item)
        return durability is not None and durability.is_usable(minimum_remaining)

    def current_item_is_usable(
        self,
        minimum_remaining: int = 1,
    ) -> bool:
        """Return whether the currently held item still has enough durability left."""
        return self.item_is_usable(self.current_item(), minimum_remaining=minimum_remaining)

    def current_offhand_item_is_usable(
        self,
        minimum_remaining: int = 1,
    ) -> bool:
        """Return whether the current off-hand item still has enough durability left."""
        return self.item_is_usable(
            self.current_offhand_item(),
            minimum_remaining=minimum_remaining,
        )
