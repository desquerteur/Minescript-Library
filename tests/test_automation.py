"""Offline regression checks. Never imports or controls the real game bridge."""

import queue
import sys
from types import SimpleNamespace as NS
from unittest.mock import Mock, call

import pytest

api = Mock()
sys.modules["minescript"] = api

import autofish  # noqa: E402
import automation_common as common  # noqa: E402
import automine  # noqa: E402
import diagnose  # noqa: E402
import entityinfo  # noqa: E402
import farm  # noqa: E402
import inventory  # noqa: E402
import nearby  # noqa: E402
import shear  # noqa: E402


@pytest.fixture(autouse=True)
def game(monkeypatch):
    api.reset_mock(return_value=True, side_effect=True)
    api.screen_name.return_value = None
    api.world_info.return_value = NS(name="Test", address="localhost", dimension="overworld")
    api.player_health.return_value = 20
    api.player_position.return_value = (0, 64, 0)
    api.player_get_targeted_entity.return_value = None
    api.player_hand_items.return_value = NS(main_hand={"item": "minecraft:fishing_rod", "count": 1})
    api.EventQueue.return_value.get.side_effect = queue.Empty
    clock = NS(now=0.0)
    monkeypatch.setattr(common.time, "monotonic", lambda: clock.now)

    def sleep(seconds):
        clock.now += max(seconds, 0.001)

    monkeypatch.setattr(common.time, "sleep", sleep)
    return api


@pytest.mark.parametrize("args", [["nan"], ["inf"], ["0"], ["-1"], ["3601"], ["1", "2"]])
def test_duration_rejects_unbounded_or_invalid_input(args):
    with pytest.raises(ValueError):
        common.duration(args)


def test_hand_items_accepts_both_minescript_return_shapes():
    common.require_item("minecraft:fishing_rod")
    api.player_hand_items.return_value = NS(main_hand=NS(item="minecraft:shears", count=1))
    common.require_item("minecraft:shears")
    with pytest.raises(common.Stopped):
        common.require_item("minecraft:fishing_rod")


@pytest.mark.parametrize("reason", ["f8", "menu", "damage", "dimension", "timeout"])
def test_session_stop_releases_inputs_and_unregisters_listeners(reason):
    with pytest.raises(common.Stopped), common.Session(1) as session:
        if reason == "f8":
            api.EventQueue.return_value.get.side_effect = [NS(key=297, action=1)]
        elif reason == "menu":
            api.screen_name.return_value = "Inventory"
        elif reason == "damage":
            api.player_health.return_value = 19
        elif reason == "dimension":
            api.world_info.return_value = NS(name="Test", address="localhost", dimension="nether")
        elif reason == "timeout":
            session.deadline = -1
        session.check()
    assert api.player_press_attack.call_args == call(False)
    assert api.player_press_use.call_args == call(False)
    api.EventQueue.return_value.unregister_all.assert_called()


def test_partial_startup_failure_still_unregisters_listeners():
    api.player_health.return_value = 4
    with pytest.raises(common.Stopped), common.Session(30):
        pytest.fail("Low health must prevent startup")
    api.EventQueue.return_value.unregister_all.assert_called()


def test_use_releases_button_when_interrupted(monkeypatch):
    with common.Session(30) as session:
        monkeypatch.setattr(session, "wait", Mock(side_effect=common.Stopped("stop")))
        with pytest.raises(common.Stopped):
            session.use()
        assert api.player_press_use.call_args_list == [call(True), call(False)]


def test_mining_ignores_occluded_blocks():
    api.player_get_targeted_block.return_value = NS(position=(9, 64, 9))
    with common.Session(30) as session:
        assert not common.break_block(session, (1, 64, 0), "minecraft:stone")
        api.player_press_attack.assert_not_called()


def test_mining_does_not_attack_entities():
    api.player_get_targeted_block.return_value = NS(position=(1, 64, 0))
    api.getblock.return_value = "minecraft:stone"
    api.player_get_targeted_entity.return_value = NS(uuid="sheep")
    with common.Session(30) as session:
        assert not common.break_block(session, (1, 64, 0), "minecraft:stone")
        assert call(True) not in api.player_press_attack.call_args_list


def test_mining_stops_when_block_changes():
    api.player_get_targeted_block.return_value = NS(position=(1, 64, 0))
    api.getblock.side_effect = ["minecraft:stone", "minecraft:stone", "minecraft:air"]
    with common.Session(30) as session:
        assert common.break_block(session, (1, 64, 0), "minecraft:stone")
        assert api.player_press_attack.call_args_list == [call(True), call(False)]


def test_mining_releases_attack_when_bridge_fails():
    api.player_get_targeted_block.return_value = NS(position=(1, 64, 0))
    api.getblock.side_effect = ["minecraft:stone", "minecraft:stone", RuntimeError("disconnected")]
    with common.Session(30) as session:
        with pytest.raises(RuntimeError):
            common.break_block(session, (1, 64, 0), "minecraft:stone")
        assert api.player_press_attack.call_args == call(False)


@pytest.mark.parametrize(
    "state,expected",
    [
        ("minecraft:wheat[age=7]", True),
        ("minecraft:carrots[age=7]", True),
        ("minecraft:beetroots[age=3]", True),
        ("minecraft:potatoes[age=6]", False),
        ("minecraft:wheat[age=1]", False),
        ("minecraft:stone", False),
    ],
)
def test_only_fully_grown_supported_crops_are_selected(state, expected):
    assert farm.mature(state) is expected


def test_farm_does_not_harvest_without_hotbar_seeds(monkeypatch):
    api.player_inventory.return_value = [NS(item="minecraft:wheat_seeds", count=64, slot=9)]
    monkeypatch.setattr(
        farm, "nearby_blocks", lambda predicate: [((1, 64, 0), "minecraft:wheat[age=7]")]
    )
    with pytest.raises(common.Stopped):
        farm.main(["1"])
    api.player_inventory_select_slot.assert_not_called()
    assert call(True) not in api.player_press_attack.call_args_list


def test_farm_verifies_replanting_and_stops_on_failure(monkeypatch):
    api.player_inventory.return_value = [NS(item="minecraft:wheat_seeds", count=64, slot=1)]
    monkeypatch.setattr(
        farm, "nearby_blocks", lambda predicate: [((1, 64, 0), "minecraft:wheat[age=7]")]
    )
    monkeypatch.setattr(farm, "break_block", Mock(return_value=True))
    monkeypatch.setattr(farm, "aim_block", Mock(return_value=True))
    api.getblock.side_effect = ["minecraft:farmland[moisture=7]", "minecraft:air"]
    with pytest.raises(common.Stopped, match="Replanting failed"):
        farm.main(["30"])
    assert call(True) in api.player_press_use.call_args_list
    assert api.player_press_use.call_args == call(False)


def test_cast_tracks_new_bobber_instead_of_neighbors(monkeypatch):
    neighbor = NS(uuid="neighbor", position=(2, 64, 2))
    own = NS(uuid="own", position=(1, 65, 1))
    monkeypatch.setattr(
        autofish,
        "bobbers",
        Mock(
            side_effect=[
                {"neighbor": neighbor},
                {"neighbor": neighbor, "own": own},
            ]
        ),
    )
    with common.Session(30) as session:
        assert autofish.cast(session) == "own"


def test_cast_stops_if_ownership_is_ambiguous(monkeypatch):
    monkeypatch.setattr(
        autofish,
        "bobbers",
        Mock(
            side_effect=[
                {},
                {"a": NS(uuid="a"), "b": NS(uuid="b")},
            ]
        ),
    )
    with common.Session(30) as session:
        with pytest.raises(common.Stopped, match="Several new bobbers"):
            autofish.cast(session)


def test_block_scan_handles_negative_coordinates():
    api.player_position.return_value = (-0.25, 64, -0.25)

    def blocks(positions):
        return [
            "minecraft:stone" if tuple(pos) == (-1, 65, -1) else "minecraft:air"
            for pos in positions
        ]

    api.getblocklist.side_effect = blocks
    assert common.nearby_blocks(lambda state: state == "minecraft:stone") == [
        ((-1, 65, -1), "minecraft:stone")
    ]


def test_cleanup_attempts_remaining_releases_after_bridge_error():
    with common.Session(30):
        api.player_press_attack.side_effect = RuntimeError("disconnected")
    api.player_press_use.assert_called_with(False)
    api.EventQueue.return_value.unregister_all.assert_called()


def test_cast_times_out_without_adopting_existing_bobber(monkeypatch):
    monkeypatch.setattr(autofish, "bobbers", lambda: {"existing": NS(uuid="existing")})
    with common.Session(30) as session, pytest.raises(common.Stopped, match="No new bobber"):
        autofish.cast(session)


def test_bobber_filter_excludes_other_entities():
    api.entities.return_value = [
        NS(type="entity.minecraft.fishing_bobber", uuid="bobber"),
        NS(type="entity.minecraft.sheep", uuid="sheep"),
    ]
    assert set(autofish.bobbers()) == {"bobber"}


def test_fishing_waits_until_settled_before_reeling(monkeypatch):
    monkeypatch.setattr(autofish, "cast", lambda session: "own")

    def bobbers():
        vy = -0.2 if common.time.monotonic() >= 2.4 else 0
        return {"own": NS(velocity=(0, vy, 0))}

    monkeypatch.setattr(autofish, "bobbers", bobbers)
    with pytest.raises(common.Stopped, match="Time limit"):
        autofish.main(["4"])
    assert api.player_press_use.call_args_list.count(call(True)) == 1
    assert api.player_press_use.call_args == call(False)


def test_miner_uses_exact_block_id_and_skips_floor(monkeypatch):
    api.player_hand_items.return_value = NS(
        main_hand={"item": "minecraft:iron_pickaxe", "count": 1}
    )

    def nearby(predicate):
        assert predicate("minecraft:cobblestone")
        assert not predicate("minecraft:mossy_cobblestone")
        return [((0, 63, 0), "minecraft:cobblestone"), ((1, 65, 0), "minecraft:cobblestone")]

    monkeypatch.setattr(automine, "nearby_blocks", nearby)
    mining = Mock(return_value=True)
    monkeypatch.setattr(automine, "break_block", mining)
    with pytest.raises(common.Stopped):
        automine.main(["cobblestone", "1"])
    assert mining.call_count > 0
    assert all(item.args[1] == (1, 65, 0) for item in mining.call_args_list)


@pytest.mark.parametrize("args", [[], ["stone;give"], ["water"], ["bedrock"]])
def test_invalid_mining_targets_are_rejected(args):
    with pytest.raises(ValueError):
        automine.main(args)


def test_shearing_only_interacts_with_verified_sheep():
    api.player_hand_items.return_value = NS(main_hand={"item": "minecraft:shears", "count": 1})
    api.entities.return_value = [NS(uuid="sheep", position=(1, 64, 0))]
    api.player_get_targeted_entity.return_value = NS(uuid="sheep")
    with pytest.raises(common.Stopped):
        shear.main(["1"])
    assert api.player_press_use.call_args_list.count(call(True)) == 1


def test_shearing_does_not_use_shears_on_another_entity():
    api.player_hand_items.return_value = NS(main_hand={"item": "minecraft:shears", "count": 1})
    api.entities.return_value = [NS(uuid="sheep", position=(1, 64, 0))]
    api.player_get_targeted_entity.return_value = NS(uuid="cow")
    with pytest.raises(common.Stopped):
        shear.main(["1"])
    assert call(True) not in api.player_press_use.call_args_list


def test_farm_harvests_then_verifies_the_replanted_crop(monkeypatch):
    api.player_inventory.return_value = [NS(item="minecraft:wheat_seeds", count=64, slot=1)]
    candidates = Mock(side_effect=[[((1, 64, 0), "minecraft:wheat[age=7]")]])
    monkeypatch.setattr(
        farm, "nearby_blocks", lambda predicate: candidates() if not candidates.called else []
    )
    monkeypatch.setattr(farm, "break_block", Mock(return_value=True))
    monkeypatch.setattr(farm, "aim_block", Mock(return_value=True))
    api.getblock.side_effect = ["minecraft:farmland[moisture=7]", "minecraft:wheat[age=0]"]
    with pytest.raises(common.Stopped, match="Time limit"):
        farm.main(["2"])
    farm.break_block.assert_called_once()
    assert api.player_press_use.call_args_list.count(call(True)) == 1


def test_inventory_counts_main_storage_and_hotbar_without_armor_or_offhand():
    api.player_inventory.return_value = [
        NS(item="minecraft:wheat_seeds", count=64, slot=0),
        NS(item="minecraft:wheat_seeds", count=12, slot=9),
        NS(item="minecraft:carrot", count=4, slot=1),
        NS(item="minecraft:diamond_helmet", count=1, slot=103),
        NS(item="minecraft:wheat_seeds", count=3, slot=40),
    ]
    inventory.main(["WHEAT"])
    assert api.echo.call_args_list == [
        call("minecraft:wheat_seeds: 76"),
        call("Main inventory and hotbar: 3/36 slots used, 33 free."),
    ]


def test_nearby_caps_output_and_filters_before_displaying():
    api.entities.return_value = [
        NS(local=True, name="Player", type="entity.minecraft.player"),
        NS(local=False, name="Cow", type="entity.minecraft.cow"),
    ] + [
        NS(local=False, name="Sheep", type="entity.minecraft.sheep", position=(1, 64, 0))
        for _ in range(25)
    ]
    nearby.main(["16", "SHEEP"])
    assert api.echo.call_count == 21
    assert "nearest 20 of 25" in api.echo.call_args.args[0]


@pytest.mark.parametrize(
    "module,args",
    [
        (nearby, ["nan"]),
        (nearby, ["65"]),
        (nearby, ["0"]),
        (entityinfo, ["inf"]),
        (entityinfo, ["-1"]),
        (diagnose, ["unexpected"]),
        (inventory, ["wheat", "extra"]),
    ],
)
def test_information_tools_reject_invalid_arguments_before_reading_game(module, args):
    with pytest.raises(ValueError):
        module.main(args)
    assert not api.mock_calls


def test_entity_information_handles_no_target():
    api.player_get_targeted_entity.return_value = None
    entityinfo.main([])
    assert "Look directly at an entity" in api.echo.call_args.args[0]


def test_entity_information_handles_an_entity_without_health():
    api.player_get_targeted_entity.return_value = NS(
        name="Dropped item",
        type="entity.minecraft.item",
        position=(1, 64, 0),
        health=None,
        uuid="item-uuid",
    )
    entityinfo.main(["8"])
    assert not any(item.args[0].startswith("Health:") for item in api.echo.call_args_list)
    api.player_press_attack.assert_not_called()
    api.player_press_use.assert_not_called()


def test_diagnostics_reports_versions_without_dumping_configuration():
    api.version_info.return_value = NS(
        minecraft="26.3",
        minescript="5.0",
        mod_loader="Fabric",
        os_name="Windows",
    )
    diagnose.main([])
    assert call("Minescript: 5.0") in api.echo.call_args_list
    assert {item[0] for item in api.mock_calls} == {"version_info", "echo"}


def test_readme_catalog_lists_all_commands_and_shared_helper():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    for script in root.glob("*.py"):
        assert f"[{script.name}]({script.name})" in readme, f"Missing catalog entry: {script.name}"
