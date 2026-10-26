"""Offline behavior tests. This fake bridge never connects to Minecraft."""

import math
import queue
import sys
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, Mock, call

import pytest

api = MagicMock()
sys.modules["minescript"] = api

import travel
import travel_common as common
import travel_elytra as elytra


@pytest.fixture(autouse=True)
def game(monkeypatch):
    api.reset_mock(return_value=True, side_effect=True)
    player = NS(position=(0.5, 64, 0.5), velocity=(0, 0, 0), health=20)
    api.player.return_value = player
    api.player_position.side_effect = lambda: player.position
    api.player_orientation.return_value = (0, 0)
    api.world_info.return_value = NS(name="Test", address="local", dimension="minecraft:overworld")
    api.screen_name.return_value = None
    api.job_info.return_value = []
    api.player_inventory.return_value = []
    api.player_inventory_select_slot.return_value = 4

    def selected_hand():
        selected = api.player_inventory_select_slot.call_args
        slot = selected.args[0] if selected else 0
        items = api.player_inventory.return_value
        found = next((item for item in items if common.field(item, "slot") == slot), None)
        # Main-storage swaps in the tests return hotbar slot 2.
        if found is None and items and api.player_inventory_slot_to_hotbar.called:
            found = items[0]
        return NS(main_hand=found)

    api.player_hand_items.side_effect = selected_hand
    api.EventQueue.return_value.get.side_effect = queue.Empty
    clock = NS(now=0.0)
    monkeypatch.setattr(common.time, "monotonic", lambda: clock.now)
    monkeypatch.setattr(
        common.time, "sleep", lambda seconds: setattr(clock, "now", clock.now + max(seconds, 0.001))
    )
    client = NS(
        food_level=Mock(return_value=20),
        grounded=Mock(return_value=True),
        flying=Mock(return_value=True),
        wings_remaining=Mock(return_value=400),
        creative_flying=Mock(return_value=False),
        prepare_glide=Mock(),
        request_glide=Mock(return_value=False),
    )
    monkeypatch.setattr(travel, "Client", lambda: client)
    monkeypatch.setattr(elytra, "Client", lambda: client)
    return NS(player=player, clock=clock, client=client)


def flat_blocks(positions):
    return ["minecraft:stone" if p[1] <= 63 else "minecraft:air" for p in positions]


def world(changes=None, radius=8):
    changes = changes or {}
    return travel.Terrain(
        {
            (x, y, z): changes.get((x, y, z), "minecraft:stone" if y <= 63 else "minecraft:air")
            for x in range(-radius, radius + 1)
            for z in range(-radius, radius + 1)
            for y in range(61, 69)
        }
    )


@pytest.mark.parametrize(
    "args,expected",
    [
        (["100", "-50"], common.Destination(100, -50)),
        (["100", "64", "-50"], common.Destination(100, -50, 64)),
        (["~10", "~", "~-3"], common.Destination(10.5, -2.5, 64)),
        (["~", "~"], common.Destination(0.5, 0.5)),
    ],
)
def test_destination_arguments(args, expected):
    assert common.arguments(args).destination == expected


@pytest.mark.parametrize(
    "args",
    [
        ["1"],
        ["1", "2", "3", "4"],
        ["nan", "1"],
        ["inf", "2"],
        ["30000000", "1"],
        ["1", "3000", "1"],
        ["a", "1"],
        ["1", "1", "--eat-at", "0"],
        ["1", "1", "--eat-at", "20"],
    ],
)
def test_bad_coordinates_do_not_press_any_inputs(args):
    with pytest.raises(ValueError):
        common.arguments(args)
    api.player_press_forward.assert_not_called()
    api.player_press_use.assert_not_called()


@pytest.mark.parametrize("state", ["minecraft:air", "minecraft:cave_air", "minecraft:short_grass"])
def test_clear_ground_space(state):
    assert travel.passable(state)


@pytest.mark.parametrize(
    "state",
    [
        "minecraft:water",
        "minecraft:lava",
        "minecraft:powder_snow",
        "minecraft:cactus",
        "minecraft:oak_slab[type=bottom]",
        "minecraft:oak_fence",
        "unknown",
    ],
)
def test_unsafe_ground_is_not_a_floor(state):
    assert not travel.support(state)


@pytest.mark.parametrize(
    "state",
    [
        "minecraft:grass_block",
        "minecraft:gravel",
        "minecraft:oak_planks",
        "minecraft:oak_slab[type=double]",
        "minecraft:crimson_stem",
    ],
)
def test_supported_full_floors(state):
    assert travel.support(state)


def test_crop_stems_are_not_mistaken_for_nether_tree_trunks():
    assert not travel.support("minecraft:pumpkin_stem[age=7]")


def test_astar_walks_around_a_wall_without_entering_it():
    wall = {(1, y, z): "minecraft:stone" for y in (64, 65, 66) for z in (-1, 0, 1)}
    terrain = world(wall)
    path = travel.plan(terrain, (0, 64, 0), common.Destination(4.5, 0.5, 64))
    assert path[-1] == (4, 64, 0)
    assert any(abs(p[2]) >= 2 for p in path)
    assert all(terrain.standable(p) for p in path)
    assert len(path) == len(set(path))


def test_astar_can_climb_and_descend_one_block():
    terrain = world({(1, 64, z): "minecraft:stone" for z in range(-8, 9)})
    path = travel.plan(terrain, (0, 64, 0), common.Destination(2.5, 0.5, 64))
    assert (1, 65, 0) in path
    assert path[-1] == (2, 64, 0)


def test_astar_rejects_jump_without_overhead_clearance():
    terrain = world({(1, 64, 0): "minecraft:stone", (0, 66, 0): "minecraft:stone"})
    assert not terrain.edge((0, 64, 0), (1, 65, 0))


def test_astar_avoids_liquids_and_cliffs():
    terrain = world(
        {
            (1, 63, 0): "minecraft:water",
            (2, 63, 0): "minecraft:air",
            (2, 62, 0): "minecraft:air",
            (2, 61, 0): "minecraft:air",
        }
    )
    path = travel.plan(terrain, (0, 64, 0), common.Destination(3.5, 0.5, 64))
    assert (1, 64, 0) not in path
    assert not any(p[0] == 2 and p[2] == 0 for p in path)


def test_long_route_returns_a_frontier_inside_the_scan():
    path = travel.plan(world(radius=8), (0, 64, 0), common.Destination(10000, 0))
    assert path[-1][0] == 8
    assert len(path) <= 16


def test_no_route_is_reported_without_movement():
    terrain = world(
        {
            (x, y, z): "minecraft:stone"
            for x, z in ((1, 0), (-1, 0), (0, 1), (0, -1))
            for y in (64, 65, 66)
        }
    )
    with pytest.raises(common.Stopped, match="No walking route"):
        travel.plan(terrain, (0, 64, 0), common.Destination(100, 0))
    api.player_press_forward.assert_not_called()


@pytest.mark.parametrize("reason", ["f8", "menu", "damage", "dimension"])
def test_stop_releases_all_owned_controls(game, reason):
    with pytest.raises(common.Stopped), common.Session(game.client) as session:
        if reason == "f8":
            api.EventQueue.return_value.get.side_effect = [NS(key=297, action=1)]
        elif reason == "menu":
            api.screen_name.return_value = "Chat"
        elif reason == "damage":
            game.player.health = 19
        else:
            api.world_info.return_value = NS(name="Test", address="local", dimension="nether")
        session.check(force=True)
    for name in ("forward", "jump", "sprint", "use", "attack"):
        assert getattr(api, "player_press_" + name).call_args == call(False)
    api.EventQueue.return_value.unregister_all.assert_called()


def test_low_health_start_still_cleans_up(game):
    game.player.health = 5
    with pytest.raises(common.Stopped), common.Session(game.client):
        pytest.fail("Must not start")
    api.EventQueue.return_value.unregister_all.assert_called_once()


def test_cleanup_continues_when_one_control_call_fails(game):
    api.player_press_forward.side_effect = RuntimeError("disconnected")
    with common.Session(game.client):
        pass
    api.player_press_use.assert_called_with(False)
    api.EventQueue.return_value.unregister_all.assert_called_once()


def test_another_traveler_is_not_interrupted():
    api.job_info.return_value = [
        NS(self=False, command=["Minescript-Library/travel.py", "1", "2"], job_id=7)
    ]
    with pytest.raises(common.Stopped, match="job 7"):
        common.exclusive()
    api.player_press_forward.assert_not_called()


def test_hotbar_food_is_eaten_until_hunger_increases_and_old_slot_restored(game):
    api.player_inventory.return_value = [NS(item="minecraft:cooked_beef", count=3, slot=1)]
    game.client.food_level.side_effect = [14, 14, 14, 20, 20]
    with common.Session(game.client) as session:
        session.eat()
    assert api.player_inventory_select_slot.call_args_list == [call(1), call(4)]
    assert call(True) in api.player_press_use.call_args_list
    assert api.player_press_use.call_args == call(False)


def test_food_can_be_taken_from_main_inventory(game):
    api.player_inventory.return_value = [{"item": "minecraft:bread", "count": 4, "slot": 20}]
    api.player_inventory_slot_to_hotbar.return_value = 2
    game.client.food_level.side_effect = [14, 20, 20]
    with common.Session(game.client) as session:
        session.eat()
    api.player_inventory_slot_to_hotbar.assert_called_once_with(20)
    assert api.player_inventory_select_slot.call_args_list == [call(2), call(4)]


@pytest.mark.parametrize(
    "bad_food", ["rotten_flesh", "pufferfish", "chorus_fruit", "spider_eye", "suspicious_stew"]
)
def test_harmful_and_teleporting_food_is_not_selected(game, bad_food):
    game.client.food_level.return_value = 10
    api.player_inventory.return_value = [NS(item="minecraft:" + bad_food, count=4, slot=0)]
    with common.Session(game.client) as session, pytest.raises(common.NoFood):
        session.eat()
    assert call(True) not in api.player_press_use.call_args_list


def test_full_hunger_does_not_use_or_change_the_held_item(game):
    with common.Session(game.client) as session:
        session.eat()
    assert call(True) not in api.player_press_use.call_args_list
    api.player_inventory_select_slot.assert_not_called()


def test_failed_eating_has_a_timeout_and_restores_slot(game):
    game.client.food_level.return_value = 14
    api.player_inventory.return_value = [NS(item="minecraft:bread", count=2, slot=0)]
    with (
        common.Session(game.client) as session,
        pytest.raises(common.Stopped, match="Eating did not"),
    ):
        session.eat()
    assert game.clock.now < 8
    api.player_inventory_select_slot.assert_called_with(4)
    api.player_press_use.assert_called_with(False)


def test_steering_callback_runs_while_eating_in_flight(game):
    api.player_inventory.return_value = [NS(item="minecraft:bread", count=2, slot=0)]
    game.client.food_level.side_effect = [14, 14, 20, 20]
    steering = Mock()
    with common.Session(game.client) as session:
        session.eat(on_tick=steering)
    steering.assert_called()


def test_walking_rechecks_changed_floor_before_pressing_forward(game):
    api.getblocklist.side_effect = lambda positions: ["minecraft:air"] * len(positions)
    with common.Session(game.client) as session:
        assert not travel.move(session, (0, 64, 0), (0, 64, 1))
    assert call(True) not in api.player_press_forward.call_args_list


def test_ground_travel_reaches_destination_in_a_simulated_world(game, monkeypatch):
    api.getblocklist.side_effect = flat_blocks
    heading = NS(x=0.5, z=0.5)
    api.player_look_at.side_effect = lambda x, y, z: (
        setattr(heading, "x", x),
        setattr(heading, "z", z),
    )

    def sleep(seconds):
        game.clock.now += max(seconds, 0.001)
        if api.player_press_forward.call_args == call(True):
            x, y, z = game.player.position
            dx, dz = heading.x - x, heading.z - z
            distance = math.hypot(dx, dz)
            travel_distance = min(distance, 4.3 * seconds)
            if distance:
                game.player.position = (
                    x + dx / distance * travel_distance,
                    y,
                    z + dz / distance * travel_distance,
                )

    monkeypatch.setattr(common.time, "sleep", sleep)
    travel.main(["0", "64", "3"])
    assert common.Destination(0, 3, 64).reached(game.player.position)
    assert call("Arrived at the walking destination.") in api.echo.call_args_list
    api.player_press_forward.assert_called_with(False)
    assert call(True) not in api.player_press_attack.call_args_list


def test_walking_read_only_check_issues_no_inputs():
    api.getblocklist.side_effect = flat_blocks
    travel.main(["0", "64", "5", "--check"])
    api.player_press_forward.assert_not_called()
    api.player_press_use.assert_not_called()


@pytest.mark.parametrize(
    "nbt,allowed",
    [
        (None, True),
        ("{explosions:[]}", True),
        ('{"explosions": [ ]}', True),
        ("{explosions:[{colors:[I;123]}]}", False),
        ("{Explosions:[{}]}", False),
    ],
)
def test_explosive_rockets_are_not_selected(nbt, allowed):
    api.player_inventory.return_value = [
        NS(item="minecraft:firework_rocket", count=64, slot=0, nbt=nbt)
    ]
    assert bool(elytra.rockets()) is allowed


def test_rockets_are_not_used_on_the_ground(game):
    game.client.flying.return_value = False
    with common.Session(game.client) as session, pytest.raises(common.Stopped, match="not gliding"):
        elytra.Flight(session, common.Destination(100, 0), 50).boost()
    assert call(True) not in api.player_press_use.call_args_list


def test_rocket_use_releases_button_and_restores_hotbar(game):
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=2)]
    with common.Session(game.client) as session:
        assert elytra.Flight(session, common.Destination(100, 0), 50).boost()
    assert api.player_inventory_select_slot.call_args_list == [call(2), call(4)]
    assert api.player_press_use.call_args_list[:2] == [call(True), call(False)]


def test_takeoff_checks_overhead_before_any_jump(game):
    game.client.flying.return_value = False
    api.getblocklist.side_effect = lambda positions: ["minecraft:stone"] * len(positions)
    with common.Session(game.client) as session, pytest.raises(common.Stopped, match="clear space"):
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    assert call(True) not in api.player_press_jump.call_args_list


def test_failed_elytra_open_does_not_fire_a_rocket(game):
    game.client.flying.return_value = False
    api.getblocklist.side_effect = flat_blocks
    with (
        common.Session(game.client) as session,
        pytest.raises(common.Stopped, match="Jump did not leave"),
    ):
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    assert call(True) not in api.player_press_use.call_args_list
    api.player_press_jump.assert_called_with(False)


def test_climb_is_limited_and_landing_flares_when_fast():
    target = common.Destination(0, 100, 64)
    assert elytra.flight_angles((0, 64, 0), (0, 0, 1), target, 200) == (0, -35)
    assert elytra.flight_angles((0, 68, 95), (0, -0.3, 1), target, 120, True)[1] < 0
    assert 0 <= elytra.flight_angles((0, 68, 95), (0, -0.1, 0.1), target, 120, True)[1] <= 5


def test_landing_area_accepts_a_clear_flat_pad():
    api.getblocklist.side_effect = flat_blocks
    target = elytra.landing_area(common.Destination(0, 0, 64), (0, 100, 0))
    assert target == common.Destination(0.5, 0.5, 64)


def test_landing_area_rejects_liquid_or_holes():
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:water" if p[1] == 63 else "minecraft:air" for p in positions
    ]
    with pytest.raises(common.Stopped, match="No flat"):
        elytra.landing_area(common.Destination(0, 0, 64), (0, 100, 0))


def test_close_flight_obstacle_returns_control(game):
    game.player.position, game.player.velocity = (0, 100, 0), (0, 0, 1)
    api.getblocklist.side_effect = lambda positions: ["minecraft:stone"] * len(positions)
    with (
        common.Session(game.client) as session,
        pytest.raises(common.Stopped, match="Obstacle immediately"),
    ):
        elytra.Flight(session, common.Destination(0, 1000), 50).obstacles()


def test_flight_read_only_check_does_not_start_flying():
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]
    elytra.main(["100", "64", "100", "--check"])
    api.player_press_jump.assert_not_called()
    api.player_press_use.assert_not_called()


def test_java_reader_uses_actual_player_food_and_equipped_wings(monkeypatch):
    chest = MagicMock()
    chest.isEmpty.return_value = False
    chest.getItem.return_value.equals.return_value = True
    chest.getMaxDamage.return_value = 432
    chest.getDamageValue.return_value = 32
    player = NS(
        getFoodData=lambda: NS(getFoodLevel=lambda: 14),
        onGround=lambda: True,
        isFallFlying=lambda: False,
        getItemBySlot=Mock(return_value=chest),
    )
    classes = {
        "net.minecraft.client.Minecraft": NS(getInstance=lambda: NS(player=player)),
        "net.minecraft.world.entity.EquipmentSlot": NS(CHEST="chest"),
        "net.minecraft.world.item.Items": NS(ELYTRA="elytra"),
    }
    monkeypatch.setitem(sys.modules, "java", NS(JavaClass=lambda name: classes[name]))
    client = common.Client()
    assert client.food_level() == 14
    assert client.grounded() is True
    assert client.flying() is False
    assert client.wings_remaining() == 400
    player.getItemBySlot.assert_called_once_with("chest")
    chest.getDamageValue.return_value = 432
    with pytest.raises(common.Stopped, match="broken"):
        client.wings_remaining()
    chest.isEmpty.return_value = True
    with pytest.raises(common.Stopped, match="Equip an Elytra"):
        client.wings_remaining()


@pytest.mark.parametrize("value", [None, -1, 21, True, "14"])
def test_missing_or_invalid_hunger_is_not_assumed_full(value):
    client = object.__new__(common.Client)
    client.hunger = lambda: value
    with pytest.raises(common.Stopped, match="read hunger"):
        client.food_level()


def test_food_selection_failure_does_not_use_another_item(game):
    api.player_inventory.return_value = [NS(item="minecraft:bread", count=2, slot=0)]
    api.player_hand_items.return_value = NS(main_hand={"item": "minecraft:stone", "count": 1})
    api.player_hand_items.side_effect = None
    game.client.food_level.return_value = 14
    with (
        common.Session(game.client) as session,
        pytest.raises(common.Stopped, match="did not appear"),
    ):
        session.eat()
    assert call(True) not in api.player_press_use.call_args_list
    api.player_inventory_select_slot.assert_called_with(4)


def test_eating_more_than_one_item_when_hunger_is_very_low(game):
    api.player_inventory.return_value = [NS(item="minecraft:cooked_beef", count=3, slot=0)]
    game.client.food_level.side_effect = [4, 4, 12, 12, 12, 20, 20]
    with common.Session(game.client) as session:
        session.eat()
    assert api.player_press_use.call_args_list.count(call(True)) == 2
    assert api.player_inventory_select_slot.call_args_list == [call(0), call(4), call(0), call(4)]


def test_stopping_during_airborne_eating_releases_use_and_restores_slot(game):
    api.player_inventory.return_value = [NS(item="minecraft:bread", count=2, slot=0)]
    game.client.food_level.return_value = 14
    with common.Session(game.client) as session, pytest.raises(common.Stopped, match="stop flight"):
        session.eat(on_tick=Mock(side_effect=common.Stopped("stop flight")))
    api.player_press_use.assert_called_with(False)
    api.player_inventory_select_slot.assert_called_with(4)


def test_advanced_obstacle_causes_a_climb_before_near_collision(game):
    game.player.position, game.player.velocity = (0, 120, 0), (0, 0, 1)
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:stone" if p[2] == 16 else "minecraft:air" for p in positions
    ]
    with common.Session(game.client) as session:
        flight = elytra.Flight(session, common.Destination(0, 1000), 50)
        flight.steer()
    assert api.player_set_orientation.call_args.args[1] == -40


@pytest.mark.parametrize("shortage", [None, "fuel", "wings", "food"])
def test_flight_transitions_to_landing_and_then_walking(game, monkeypatch, shortage):
    """Test controller transitions, not Minecraft's flight physics."""
    game.player.position, game.player.velocity = (0.5, 120, 0.5), (0, 0, 1)
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]
    game.client.grounded.side_effect = lambda: game.player.position[1] <= 64
    game.client.flying.side_effect = lambda: game.player.position[1] > 64
    api.getblocklist.side_effect = flat_blocks
    if shortage == "wings":
        game.client.wings_remaining.side_effect = [100, 50, 50, 50, 50, 50, 50]
    if shortage == "food":
        game.client.food_level.return_value = 14
    finish_walk = Mock()
    monkeypatch.setattr(elytra, "walk_main", finish_walk)
    landings = []
    original = elytra.Flight.begin_landing

    def begin_landing(self, *, fallback=False):
        landings.append(fallback)
        return original(self, fallback=fallback)

    monkeypatch.setattr(elytra.Flight, "begin_landing", begin_landing)

    def sleep(seconds):
        game.clock.now += max(seconds, 0.001)
        x, y, z = game.player.position
        if landings:
            y = max(64, y - seconds * 15)
        else:
            z += seconds * 30
        game.player.position = (x, y, z)
        if shortage == "fuel" and call(True) in api.player_press_use.call_args_list:
            api.player_inventory.return_value = []

    monkeypatch.setattr(common.time, "sleep", sleep)
    elytra.main(["0", "64", "200"])
    finish_walk.assert_called_once_with(["0", "64", "200", "--eat-at", "14"])
    assert landings == [shortage is not None]
    assert game.player.position[1] == 64
    api.player_press_use.assert_called_with(False)


def test_flight_stop_does_not_start_walking_in_midair(game, monkeypatch):
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]
    monkeypatch.setattr(elytra.Flight, "fly", Mock(side_effect=common.Stopped("F8")))
    finish_walk = Mock()
    monkeypatch.setattr(elytra, "walk_main", finish_walk)
    with pytest.raises(common.Stopped, match="F8"):
        elytra.main(["100", "64", "100"])
    finish_walk.assert_not_called()
    api.player_press_use.assert_called_with(False)


def walking_simulation(game, monkeypatch, *, delayed_scans=False, hunger=False):
    """Move on a fixed heading while forward is held, including during API calls.

    Looking at a point does not magically stop the simulated player at that point.
    This exposes waypoint overshoot and pauses that a clamped-position fake hides.
    """
    state = NS(
        forward=False,
        use=False,
        direction=(0, 1),
        transitions=[],
        moving_scans=0,
        looks=[],
        hunger=20,
        hungry_once=False,
        food_ready=None,
    )

    def advance(seconds):
        game.clock.now += max(seconds, 0.001)
        if state.forward:
            x, y, z = game.player.position
            dx, dz = state.direction
            game.player.position = (x + dx * 4.3 * seconds, y, z + dz * 4.3 * seconds)
        if hunger and not state.hungry_once and game.clock.now >= 2:
            state.hunger, state.hungry_once = 14, True
        if state.food_ready is not None and game.clock.now >= state.food_ready:
            state.hunger = 20

    def forward(held):
        state.transitions.append((held, game.player.position))
        state.forward = held

    def use(held):
        assert not held or not state.forward, "Eating must pause walking"
        state.use = held
        if held:
            state.food_ready = game.clock.now + 1.6

    def look(x, y, z):
        px, _, pz = game.player.position
        dx, dz = x - px, z - pz
        length = math.hypot(dx, dz)
        state.direction = dx / length, dz / length
        state.looks.append((dx, dz))

    def blocks(positions):
        if delayed_scans and len(positions) > 1000:
            state.moving_scans += int(state.forward)
            advance(0.18)
        return flat_blocks(positions)

    api.player_press_forward.side_effect = forward
    api.player_press_use.side_effect = use
    api.player_look_at.side_effect = look
    api.getblocklist.side_effect = blocks
    game.client.food_level.side_effect = lambda: state.hunger
    monkeypatch.setattr(common.time, "sleep", advance)
    return state


@pytest.mark.parametrize(
    "destination", [common.Destination(0, 40, 64), common.Destination(30, 30, 64)]
)
def test_level_walk_holds_forward_across_blocks_and_delayed_route_refreshes(
    game, monkeypatch, destination
):
    state = walking_simulation(game, monkeypatch, delayed_scans=True)
    travel.main([str(destination.x), str(destination.y), str(destination.z)])
    assert destination.reached(game.player.position)
    assert [held for held, _ in state.transitions].count(True) == 1
    assert state.moving_scans >= 2
    assert all(destination.reached(pos) for held, pos in state.transitions if not held)
    assert all(dz > 0 for _, dz in state.looks), "Do not turn back toward passed waypoints"


def test_continuous_walk_pauses_for_food_then_resumes(game, monkeypatch):
    state = walking_simulation(game, monkeypatch, hunger=True)
    api.player_inventory.return_value = [NS(item="minecraft:cooked_beef", count=3, slot=0)]
    travel.main(["0", "64", "40"])
    # One continuous hold before eating and one after; no per-block pulses.
    assert [held for held, _ in state.transitions].count(True) == 2
    assert call(True) in api.player_press_use.call_args_list
    assert common.Destination(0, 40, 64).reached(game.player.position)
    assert state.hunger == 20


def test_changed_floor_stops_continuous_walking_before_the_hazard(game, monkeypatch):
    state = walking_simulation(game, monkeypatch)

    def blocks(positions):
        return [
            "minecraft:water"
            if tuple(p) == (0, 63, 2) and game.clock.now >= 0.15
            else "minecraft:stone"
            if p[1] <= 63
            else "minecraft:air"
            for p in positions
        ]

    api.getblocklist.side_effect = blocks
    with common.Session(game.client) as session:
        walker = travel.Walker(session)
        completed, blocked = walker.follow((0, 64, 0), [(0, 64, z) for z in range(1, 9)])
        assert blocked
        assert not walker.walking
        assert game.player.position[2] < 2
    assert [held for held, _ in state.transitions][:2] == [True, False]


def test_f8_interrupts_a_held_forward_key(game, monkeypatch):
    state = walking_simulation(game, monkeypatch)

    def event(*args, **kwargs):
        if game.clock.now >= 0.3:
            return NS(key=297, action=1)
        raise queue.Empty

    api.EventQueue.return_value.get.side_effect = event
    with pytest.raises(common.Stopped, match="F8"):
        travel.main(["0", "64", "40"])
    assert not state.forward
    assert [held for held, _ in state.transitions].count(True) == 1


def test_diagonal_route_is_straight_on_open_ground():
    path = travel.plan(world(), (0, 64, 0), common.Destination(7, 7, 64))
    assert path == [(n, 64, n) for n in range(1, 8)]


@pytest.mark.parametrize(
    "change",
    [
        {(1, 63, 0): "minecraft:water"},
        {(1, 64, 0): "minecraft:stone"},
        {(0, 65, 1): "minecraft:stone"},
    ],
)
def test_diagonal_edges_cannot_cut_a_corner_or_missing_side_floor(change):
    assert not world(change).edge((0, 64, 0), (1, 64, 1))


def test_waypoint_plane_accepts_a_small_overshoot_without_aiming_back():
    assert travel.passed((0.5, 64, 1.8), (0, 64, 0), (0, 64, 1))
    assert not travel.passed((1.2, 64, 1.8), (0, 64, 0), (0, 64, 1))
    assert not travel.passed((0.5, 64, 50), (0, 64, 0), (0, 64, 1))


@pytest.mark.parametrize("jump_delay", [0.03, 0.75])
def test_launch_waits_for_airborne_state_then_confirms_gliding_before_boost(
    game, monkeypatch, jump_delay
):
    api.getblocklist.side_effect = flat_blocks
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]
    state = NS(jumped_at=None, requested_at=None, prepared=False, boosted_at=None)

    def prepare():
        state.prepared = True

    def jump(pressed):
        if pressed:
            assert state.prepared, "Prepare reflection before the airborne window"
            state.jumped_at = game.clock.now

    def grounded():
        return state.jumped_at is None or game.clock.now - state.jumped_at < jump_delay

    def request():
        assert not grounded(), "Do not send a launch request on the ground"
        state.requested_at = game.clock.now
        return True

    def flying():
        return state.requested_at is not None and game.clock.now - state.requested_at >= 0.09

    def use(pressed):
        if pressed:
            assert flying()
            assert game.clock.now - state.requested_at >= 0.21
            state.boosted_at = game.clock.now

    game.client.prepare_glide.side_effect = prepare
    game.client.grounded.side_effect = grounded
    game.client.request_glide.side_effect = request
    game.client.flying.side_effect = flying
    api.player_press_jump.side_effect = jump
    api.player_press_use.side_effect = use
    with common.Session(game.client) as session:
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    assert api.player_press_jump.call_args_list.count(call(True)) == 1
    assert state.boosted_at is not None
    game.client.request_glide.assert_called_once()
    api.player_press_jump.assert_called_with(False)


def test_active_creative_flight_has_a_specific_message_and_no_takeoff(game):
    game.client.flying.return_value = False
    game.client.creative_flying.return_value = True
    with (
        common.Session(game.client) as session,
        pytest.raises(common.Stopped, match="Creative flight is active"),
    ):
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    game.client.prepare_glide.assert_not_called()
    assert call(True) not in api.player_press_jump.call_args_list
    assert call(True) not in api.player_press_use.call_args_list


def test_refused_glide_request_never_uses_a_rocket(game):
    api.getblocklist.side_effect = flat_blocks
    game.client.flying.return_value = False
    game.client.grounded.return_value = False
    with (
        common.Session(game.client) as session,
        pytest.raises(common.Stopped, match="did not open and stay"),
    ):
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    assert 1 <= game.client.request_glide.call_count <= 14
    assert call(True) not in api.player_press_use.call_args_list
    assert call(True) not in api.player_press_jump.call_args_list


def test_transient_glide_flag_is_not_treated_as_a_confirmed_launch(game):
    api.getblocklist.side_effect = flat_blocks
    game.client.grounded.return_value = False
    state = NS(requested_at=None)

    def request():
        state.requested_at = game.clock.now
        return True

    game.client.request_glide.side_effect = request
    game.client.flying.side_effect = lambda: (
        state.requested_at is not None and game.clock.now - state.requested_at < 0.06
    )
    with (
        common.Session(game.client) as session,
        pytest.raises(common.Stopped, match="did not open and stay"),
    ):
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    assert call(True) not in api.player_press_use.call_args_list


def test_f8_during_jump_releases_space_and_does_not_boost(game):
    api.getblocklist.side_effect = flat_blocks
    game.client.flying.return_value = False

    def event(*args, **kwargs):
        if game.clock.now >= 0.2:
            return NS(key=297, action=1)
        raise queue.Empty

    api.EventQueue.return_value.get.side_effect = event
    with common.Session(game.client) as session, pytest.raises(common.Stopped, match="F8"):
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    api.player_press_jump.assert_called_with(False)
    assert call(True) not in api.player_press_use.call_args_list


def test_native_glide_request_uses_vanilla_eligibility_and_sends_only_when_accepted(monkeypatch):
    sent = Mock()
    allowed = Mock(side_effect=[False, True, False])
    player = NS(tryToStartFallFlying=allowed, connection=NS(send=sent))
    packet = object()
    packet_type = Mock(return_value=packet)
    classes = {
        "net.minecraft.network.protocol.game.ServerboundPlayerCommandPacket": packet_type,
        "net.minecraft.network.protocol.game.ServerboundPlayerCommandPacket$Action": NS(
            START_FALL_FLYING="glide"
        ),
    }
    monkeypatch.setitem(sys.modules, "java", NS(JavaClass=lambda name: classes[name]))
    client = object.__new__(common.Client)
    client.player, client._glide_packet = player, None
    client.prepare_glide()
    assert client.request_glide() is False
    assert client.request_glide() is True
    assert client.request_glide() is False
    packet_type.assert_called_once_with(player, "glide")
    sent.assert_called_once_with(packet)


def test_creative_flight_reader_checks_live_ability_state():
    abilities = NS(flying=False)
    client = object.__new__(common.Client)
    client.player = NS(getAbilities=lambda: abilities)
    assert client.creative_flying() is False
    abilities.flying = True
    assert client.creative_flying() is True
