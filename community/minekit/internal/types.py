"""Small shared types for the DX layer."""

from dataclasses import dataclass
from typing import Tuple

BlockPos = Tuple[int, int, int]
Vec3 = Tuple[float, float, float]
YawPitch = Tuple[float, float]


@dataclass(frozen=True)
class ItemDurability:
    """Durability snapshot parsed from an item's NBT/components."""

    damage: int | None
    max_damage: int | None
    remaining: int | None
    ratio: float | None

    def has_remaining(self, minimum: int = 1) -> bool:
        """Return ``True`` when the item has more than ``minimum`` durability left."""
        return self.remaining is not None and self.remaining > int(minimum)

    def is_usable(self, minimum_remaining: int = 1) -> bool:
        """Return whether the item is still safe to use.

        This is an ergonomic alias for ``has_remaining(...)``.
        """
        return self.has_remaining(minimum_remaining)


@dataclass(frozen=True)
class InventoryItem:
    """Typed view of an item stack returned by Minescript."""

    name: str | None
    count: int | None
    nbt: str | None
    slot: int | None
    selected: bool | None
    durability: ItemDurability | None


@dataclass(frozen=True)
class InventoryAggregate:
    """Aggregated view of all stacks for a given item id."""

    name: str
    total_count: int
    stack_count: int
    slots: tuple[int, ...]
    selected: bool
    stacks: tuple[InventoryItem, ...]
