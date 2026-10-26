"""Offline regression checks. Never imports or controls the real game bridge."""

import queue
import sys
from itertools import islice
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, Mock, call

import pytest

api = Mock()
sys.modules["minescript"] = api

import autofish  # noqa: E402
import automation_common as common  # noqa: E402
import automine  # noqa: E402
import bearing  # noqa: E402
import blockwatch  # noqa: E402
import branchmine  # noqa: E402
import branchplan  # noqa: E402
import chunkcoords  # noqa: E402
import cropstatus  # noqa: E402
import diagnose  # noqa: E402
import entityinfo  # noqa: E402
import equip  # noqa: E402
import farm  # noqa: E402
import inventory  # noqa: E402
import inventorywatch  # noqa: E402
import library  # noqa: E402
import library_tools  # noqa: E402
import nearby  # noqa: E402
import orescan  # noqa: E402
import pickupwatch  # noqa: E402
import regioncount  # noqa: E402
import shear  # noqa: E402
import stripmine  # noqa: E402
import worldclock  # noqa: E402


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


@pytest.mark.parametrize("args", [["nan"], ["inf"], ["-1"], ["invalid"], ["1", "2"]])
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
    with common.Session(30) as session:
        assert autofish.cast(session) is None


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


def tunnel_world(changes=None):
    changes = changes or {}

    def blocks(positions):
        return [
            changes.get(tuple(pos), "minecraft:stone" if pos[1] == 63 else "minecraft:air")
            for pos in positions
        ]

    api.getblocklist.side_effect = blocks


@pytest.mark.parametrize(
    "state",
    [
        "minecraft:lava",
        "minecraft:water",
        "minecraft:fire",
        "minecraft:oak_stairs[waterlogged=true]",
    ],
)
def test_tunnel_survey_rejects_nearby_hazards_before_any_input(state):
    tunnel_world({(1, 64, 1): state})
    with pytest.raises(common.Stopped, match="Hazard"):
        stripmine.survey((0, 64, 1))
    api.player_press_forward.assert_not_called()
    api.player_press_attack.assert_not_called()


@pytest.mark.parametrize(
    "floor",
    ["minecraft:air", "minecraft:water", "minecraft:gravel", "minecraft:oak_slab[type=bottom]"],
)
def test_tunnel_rejects_unsupported_floor(floor):
    tunnel_world({(0, 63, 1): floor})
    with pytest.raises(common.Stopped):
        stripmine.survey((0, 64, 1))


@pytest.mark.parametrize(
    "ceiling",
    [
        "minecraft:gravel",
        "minecraft:sand",
        "minecraft:red_sand",
        "minecraft:red_concrete_powder",
        "minecraft:anvil",
    ],
)
def test_tunnel_rejects_falling_ceiling(ceiling):
    tunnel_world({(0, 66, 1): ceiling})
    with pytest.raises(common.Stopped, match="Falling"):
        stripmine.survey((0, 64, 1))


def test_clear_tunnel_step_releases_forward():
    tunnel_world()
    api.player_position.side_effect = [(0.5, 64, 0.5), (0.5, 64, 1.5)]
    with common.Session(30) as session:
        stripmine.advance(session, (0, 64, 1))
        assert api.player_press_forward.call_args_list.count(call(True)) == 1
        assert api.player_press_forward.call_args == call(False)


def test_tunnel_stops_on_blocked_movement_and_releases_forward():
    tunnel_world()
    api.player_position.return_value = (0.5, 64, 0.5)
    with common.Session(30) as session, pytest.raises(common.Stopped, match="Movement blocked"):
        stripmine.advance(session, (0, 64, 1))
    assert api.player_press_forward.call_args == call(False)


def test_tunnel_will_not_mine_a_container():
    tunnel_world({(0, 65, 1): "minecraft:chest[facing=north]"})
    with common.Session(30) as session, pytest.raises(common.Stopped, match="Unsupported block"):
        stripmine.advance(session, (0, 64, 1))
    assert call(True) not in api.player_press_attack.call_args_list


def test_mining_stops_when_pickaxe_is_missing():
    with stripmine.MiningSession(30) as session, pytest.raises(common.Stopped, match="pickaxe"):
        session.check()


def test_mining_stops_with_full_inventory():
    api.player_hand_items.return_value = NS(
        main_hand={"item": "minecraft:iron_pickaxe", "count": 1}
    )
    api.player_inventory.return_value = [NS(slot=slot, count=64) for slot in range(36)]
    with (
        stripmine.MiningSession(30) as session,
        pytest.raises(common.Stopped, match="Inventory is full"),
    ):
        session.check()


@pytest.mark.parametrize("heading", [(0, 1), (-1, 0), (0, -1), (1, 0)])
def test_branch_route_returns_to_main_tunnel_after_every_pair(heading):
    steps = list(branchmine.route(heading, length=12, spacing=3, branch=4))
    assert len(steps) == 12 + 4 * 4 * 4
    x = z = 0
    for dx, dz in steps:
        x += dx
        z += dz
    assert (x, z) == (12 * heading[0], 12 * heading[1])


@pytest.mark.parametrize(
    "yaw,expected", [(0, (0, 1)), (90, (-1, 0)), (180, (0, -1)), (-90, (1, 0)), (360, (0, 1))]
)
def test_mining_uses_minecraft_cardinal_directions(yaw, expected):
    assert stripmine.direction(yaw) == expected


def test_volume_limit_is_enforced_before_query():
    with pytest.raises(ValueError, match="too large"):
        library_tools.volume((0, 0, 0), (100, 100, 100))
    api.getblocklist.assert_not_called()


def test_block_count_accepts_reversed_selection():
    api.getblocklist.return_value = ["minecraft:stone", "minecraft:stone", "minecraft:air"]
    regioncount.main(["2", "64", "0", "0", "64", "0"])
    assert call("minecraft:stone: 2") in api.echo.call_args_list


def test_chunk_coordinates_floor_negative_positions():
    api.player_position.return_value = (-0.1, 64, -16.1)
    chunkcoords.main([])
    assert call("Chunk: -1, -2; local block: 15, 15") in api.echo.call_args_list


def test_bearing_to_east_has_negative_ninety_yaw():
    bearing.main(["10", "65.62", "0"])
    assert "yaw -90.0" in api.echo.call_args.args[0]


def test_equip_uses_existing_hotbar_slot_first():
    api.player_inventory.return_value = [
        NS(item="minecraft:iron_pickaxe", count=1, slot=9),
        NS(item="minecraft:iron_pickaxe", count=1, slot=2),
    ]
    equip.main(["iron_pickaxe"])
    api.player_inventory_slot_to_hotbar.assert_not_called()
    api.player_inventory_select_slot.assert_called_once_with(2)


def test_clock_converts_midnight_correctly():
    api.world_info.return_value = NS(
        day_ticks=18000, raining=False, thundering=False, dimension="overworld"
    )
    worldclock.main([])
    assert "00:00" in api.echo.call_args_list[0].args[0]


def test_crop_status_counts_ripe_and_growing_separately(monkeypatch):
    monkeypatch.setattr(
        cropstatus,
        "around",
        lambda radius: [
            ((0, 64, 0), "minecraft:wheat[age=7]"),
            ((1, 64, 0), "minecraft:wheat[age=2]"),
        ],
    )
    cropstatus.main(["2"])
    api.echo.assert_called_once_with("minecraft:wheat: 1 ripe, 1 growing")


def test_ore_scan_excludes_ordinary_stone(monkeypatch):
    monkeypatch.setattr(
        orescan,
        "around",
        lambda radius: [((0, 64, 0), "minecraft:stone"), ((1, 64, 0), "minecraft:diamond_ore")],
    )
    orescan.main(["2"])
    assert "minecraft:diamond_ore" in api.echo.call_args_list[0].args[0]
    assert "1 ore blocks" in api.echo.call_args.args[0]


def test_branch_preview_never_sends_game_commands():
    api.player_position.return_value = (0.5, 64, 0.5)
    api.player_orientation.return_value = (0, 0)
    branchplan.main(["8", "4", "3"])
    api.execute.assert_not_called()
    api.player_press_forward.assert_not_called()


def test_catalog_contains_over_100_distinct_programs_with_valid_hashes():
    import ast
    import hashlib

    catalog = library.load_catalog()
    entries = catalog["entries"]
    assert len({entry["id"] for entry in entries}) == len(entries)
    programs = [entry for entry in entries if entry["kind"] != "support"]
    assert len(programs) > 100
    assert len(programs) == catalog["counts"]["programs"]
    fingerprints = []
    for entry in entries:
        assert entry["license"] == "MIT"
        path = library.script_path(entry)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        if entry["kind"] != "support":
            fingerprints.append(ast.dump(tree, include_attributes=False))
    assert len(set(fingerprints)) == len(fingerprints)


def test_catalog_rejects_path_traversal():
    with pytest.raises(ValueError, match="Invalid catalog path"):
        library.script_path({"path": "../../outside.py"})


def test_catalog_rejects_changed_script_hash():
    with pytest.raises(ValueError, match="changed"):
        library.script_path({"path": "library.py", "sha256": "wrong"})


def test_launcher_preserves_arguments_without_executing_them(monkeypatch):
    def launched(path, run_name):
        assert sys.argv[1:] == ["hello; unsafe", '"quoted"']
        assert run_name == "__main__"

    monkeypatch.setattr(library.runpy, "run_path", launched)
    original_args = sys.argv[:]
    library.launch(
        library.find_entry(library.load_catalog()["entries"], "diagnose"),
        ["hello; unsafe", '"quoted"'],
    )
    assert sys.argv == original_args
    api.execute.assert_not_called()


def test_stripmine_main_follows_the_requested_cardinal_route(monkeypatch):
    api.player_hand_items.return_value = NS(
        main_hand={"item": "minecraft:iron_pickaxe", "count": 1}
    )
    api.player_inventory.return_value = []
    api.player_orientation.return_value = (90, 0)
    movement = Mock()
    monkeypatch.setattr(stripmine, "advance", movement)
    stripmine.main(["3", "5"])
    assert [item.args[1] for item in movement.call_args_list] == [
        (-1, 64, 0),
        (-2, 64, 0),
        (-3, 64, 0),
    ]


def test_branchmine_main_passes_a_finite_route_and_duration(monkeypatch):
    api.player_orientation.return_value = (0, 0)
    movement = Mock()
    monkeypatch.setattr(branchmine, "follow_steps", movement)
    branchmine.main(["8", "4", "2", "5"])
    assert len(list(movement.call_args.args[0])) == 24
    assert movement.call_args.args[1] == 5


def test_blockwatch_reports_changes_and_stops_on_its_deadline():
    api.player_get_targeted_block.return_value = NS(position=(1, 64, 0))
    api.getblock.side_effect = lambda *args: (
        "minecraft:air" if common.time.monotonic() >= 0.25 else "minecraft:stone"
    )
    with pytest.raises(common.Stopped, match="Time limit"):
        blockwatch.main(["1"])
    assert any("stone -> minecraft:air" in item.args[0] for item in api.echo.call_args_list)


def test_inventorywatch_reports_supply_deltas():
    api.player_inventory.side_effect = lambda: [
        NS(item="minecraft:stone", slot=0, count=5 if common.time.monotonic() >= 0.5 else 1)
    ]
    with pytest.raises(common.Stopped, match="Time limit"):
        inventorywatch.main(["1"])
    assert call("minecraft:stone: +4; now 5") in api.echo.call_args_list


def test_pickupwatch_filters_out_other_players_pickups():
    pickups, keys = MagicMock(), Mock()
    pickups.__enter__.return_value = pickups
    keys.get.side_effect = queue.Empty
    items = iter(
        [
            NS(player_uuid="own", amount=2, item=NS(name="Iron")),
            NS(player_uuid="other", amount=99, item=NS(name="Gold")),
        ]
    )

    def next_pickup(**kwargs):
        try:
            return next(items)
        except StopIteration:
            raise queue.Empty from None

    pickups.get.side_effect = next_pickup
    api.EventQueue.side_effect = [pickups, keys]
    api.player.return_value = NS(uuid="own")
    with pytest.raises(common.Stopped, match="Time limit"):
        pickupwatch.main(["1"])
    assert call("Picked up 2: Iron") in api.echo.call_args_list
    assert not any("Gold" in item.args[0] for item in api.echo.call_args_list)


@pytest.mark.parametrize(
    "module,args",
    [
        (stripmine, ["-1"]),
        (stripmine, ["forever", "nan"]),
        (stripmine, ["1", "2", "3"]),
        (branchmine, ["1", "0"]),
        (branchmine, ["0", "4", "0"]),
        (branchplan, []),
        (chunkcoords, ["extra"]),
        (bearing, ["nan", "1", "2"]),
        (regioncount, ["1"]),
        (cropstatus, ["0"]),
        (worldclock, ["extra"]),
        (equip, []),
    ],
)
def test_new_commands_reject_invalid_input_without_world_changes(module, args):
    with pytest.raises(ValueError):
        module.main(args)
    api.execute.assert_not_called()
    api.player_press_forward.assert_not_called()
    api.player_press_attack.assert_not_called()


def test_catalog_can_be_searched_and_inspected_without_launching():
    library.main(["list", "mining"])
    assert any("stripmine" in item.args[0] for item in api.echo.call_args_list)
    library.main(["info", "stripmine"])
    api.execute.assert_not_called()


def test_support_module_cannot_be_launched():
    entry = library.find_entry(library.load_catalog()["entries"], "library_tools")
    with pytest.raises(ValueError, match="support module"):
        library.launch(entry, [])


def test_every_package_has_a_preserved_mit_notice():
    for package in library.load_catalog()["packages"]:
        notice = (library.ROOT / package["folder"] / "LICENSE").read_text(encoding="utf-8")
        assert "Permission is hereby granted" in " ".join(notice.split())
        assert "THE SOFTWARE IS PROVIDED" in notice


@pytest.mark.parametrize("args", [[], ["0"], ["0.0"], ["forever"], ["ENDLESS"], ["unlimited"]])
def test_default_and_explicit_unlimited_durations(args):
    assert common.duration(args) is None


@pytest.mark.parametrize("seconds", ["0.5", "3601", "86400"])
def test_positive_durations_have_no_arbitrary_hour_cap(seconds):
    assert common.duration([seconds]) == float(seconds)


@pytest.mark.parametrize("seconds", [None, 0])
def test_unlimited_session_runs_past_a_day_and_still_cancels(monkeypatch, seconds):
    with pytest.raises(common.Stopped, match="F8"), common.Session(seconds) as session:
        monkeypatch.setattr(common.time, "monotonic", lambda: 86401)
        session.check()
        api.player_press_forward(True)
        api.EventQueue.return_value.get.side_effect = [NS(key=297, action=1)]
        session.check()
    assert api.player_press_forward.call_args == call(False)


@pytest.mark.parametrize("args", [[], ["0"], ["forever"], ["endless"]])
def test_stripminer_defaults_to_a_lazy_endless_route(monkeypatch, args):
    api.player_orientation.return_value = (0, 0)
    movement = Mock()
    monkeypatch.setattr(stripmine, "follow_steps", movement)
    stripmine.main(args)
    steps, seconds = movement.call_args.args
    assert seconds is None
    assert iter(steps) is steps
    assert list(islice(steps, 10000)) == [(0, 1)] * 10000


def test_stripminer_explicit_length_is_still_finite_without_old_128_block_cap(monkeypatch):
    api.player_orientation.return_value = (0, 0)
    movement = Mock()
    monkeypatch.setattr(stripmine, "follow_steps", movement)
    stripmine.main(["512"])
    steps, seconds = movement.call_args.args
    assert len(list(steps)) == 512
    assert seconds is None


def test_default_branchmine_continues_past_the_old_main_tunnel_cap(monkeypatch):
    api.player_orientation.return_value = (0, 0)
    movement = Mock()
    monkeypatch.setattr(branchmine, "follow_steps", movement)
    branchmine.main([])
    steps, seconds = movement.call_args.args
    assert seconds is None
    prefix = list(islice(steps, 840))  # 30 complete 4-main-block cycles with 6-block branches.
    assert len(prefix) == 840
    assert tuple(map(sum, zip(*prefix, strict=True))) == (0, 120)
    assert next(steps) == (0, 1)


def test_branch_route_does_not_allocate_huge_branches():
    steps = branchmine.route((0, 1), length=None, spacing=1, branch=10**12)
    assert list(islice(steps, 3)) == [(0, 1), (1, 0), (1, 0)]


def test_fishing_recasts_when_a_bobber_disappears(monkeypatch):
    casting = Mock(return_value="own")
    monkeypatch.setattr(autofish, "cast", casting)
    monkeypatch.setattr(autofish, "bobbers", lambda: {})
    with pytest.raises(common.Stopped, match="Time limit"):
        autofish.main(["3"])
    assert casting.call_count >= 2


def test_fishing_retries_failed_casts_without_stopping(monkeypatch):
    casting = Mock(return_value=None)
    monkeypatch.setattr(autofish, "cast", casting)
    with pytest.raises(common.Stopped, match="Time limit"):
        autofish.main(["3"])
    assert casting.call_count >= 2


def test_fishing_recasts_after_ninety_seconds_without_a_bite(monkeypatch):
    casting = Mock(return_value="own")
    monkeypatch.setattr(autofish, "cast", casting)
    monkeypatch.setattr(autofish, "bobbers", lambda: {"own": NS(velocity=(0, 0, 0))})
    with pytest.raises(common.Stopped, match="Time limit"):
        autofish.main(["100"])
    assert casting.call_count >= 2
    assert call(True) in api.player_press_use.call_args_list


@pytest.mark.parametrize("terrain", ["minecraft:dirt", "minecraft:clay", "minecraft:gravel"])
def test_miner_can_clear_ordinary_terrain_below_a_stable_ceiling(monkeypatch, terrain):
    changes = {(0, 65, 1): terrain}
    tunnel_world(changes)
    api.player_position.return_value = (0.5, 64, 1.5)

    def mine(session, pos, state):
        changes[pos] = "minecraft:air"
        return True

    breaking = Mock(side_effect=mine)
    monkeypatch.setattr(stripmine, "break_block", breaking)
    with common.Session(30) as session:
        stripmine.advance(session, (0, 64, 1))
    breaking.assert_called_once()
