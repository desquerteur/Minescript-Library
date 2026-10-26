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

NativeFlightClass = elytra.NativeFlight
WalkLeaseClass = travel.WalkLease


class JavaInt32(int):
    """Tag explicit Java int conversions at the native API boundary."""


@pytest.fixture
def native_runtime(game):
    """Execute the shipped tick callback against native API-shaped doubles."""
    state = NS(
        grounded=True,
        flying=False,
        health=20,
        eligible=True,
        explosive=False,
        duration=1,
        accepted=True,
        slot_is_rocket=True,
    )
    listeners = {}
    api.add_event_listener.side_effect = lambda kind, callback: (
        listeners.update({kind: callback}) or len(listeners)
    )
    component = NS(
        explosions=lambda: NS(isEmpty=lambda: not state.explosive),
        flightDuration=lambda: state.duration,
    )
    stack = NS(getItem=lambda: NS(equals=lambda _: state.slot_is_rocket), get=lambda _: component)

    def start_glide():
        if not state.eligible or state.grounded:
            return False
        state.flying = True
        return True

    player = NS(
        onGround=lambda: state.grounded,
        isFallFlying=lambda: state.flying,
        getHealth=lambda: state.health,
        getMainHandItem=lambda: stack,
        tryToStartFallFlying=Mock(side_effect=start_glide),
        connection=NS(send=Mock()),
    )

    def has_chunk(x, z):
        assert type(x) is JavaInt32 and type(z) is JavaInt32
        return True

    def get_height(kind, x, z):
        assert type(x) is JavaInt32 and type(z) is JavaInt32
        return 64

    level = NS(hasChunk=has_chunk, getHeight=get_height, getMinY=lambda: -64)
    use = Mock(side_effect=lambda *args: NS(consumesAction=lambda: state.accepted))
    # Minecraft 26.3 has no public `screen` field. Keep it absent here so an
    # accidental direct access fails just as it does in the installed client.
    mc = NS(player=player, level=level, gameMode=NS(useItem=use))
    classes = {
        "net.minecraft.client.Minecraft": NS(getInstance=lambda: mc),
        "net.minecraft.network.protocol.game.ServerboundPlayerCommandPacket": lambda p, a: (p, a),
        "net.minecraft.network.protocol.game.ServerboundPlayerCommandPacket$Action": NS(
            START_FALL_FLYING="start"
        ),
        "net.minecraft.world.InteractionHand": NS(MAIN_HAND="main"),
        "net.minecraft.world.item.Items": NS(FIREWORK_ROCKET="rocket"),
        "net.minecraft.core.component.DataComponents": NS(FIREWORKS="fireworks"),
        "net.minecraft.world.level.levelgen.Heightmap$Types": NS(
            MOTION_BLOCKING_NO_LEAVES="surface"
        ),
    }
    namespace = {"JavaClass": classes.__getitem__, "JavaInt": JavaInt32}
    # Execute only the constant shipped source; no external text is evaluated.
    exec(compile(elytra.NATIVE_FLIGHT, "<native-flight>", "exec"), namespace)  # noqa: S102
    return NS(
        state=state, player=player, level=level, mc=mc, use=use, code=namespace, listeners=listeners
    )


def test_native_launch_opens_wings_and_uses_one_rocket_on_the_same_tick(native_runtime):
    native = native_runtime
    native.code["arm"]()
    native.listeners["tick"](None)
    native.use.assert_not_called()
    native.state.grounded = False
    native.listeners["tick"](None)
    assert native.code["status"] == pytest.approx(2.15)
    native.player.connection.send.assert_called_once_with((native.player, "start"))
    native.use.assert_called_once_with(native.player, "main")
    native.listeners["tick"](None)
    native.use.assert_called_once()
    api.player_press_jump.assert_called_with(False)


def test_native_menu_guard_works_without_a_minecraft_screen_field(native_runtime):
    native = native_runtime
    assert not hasattr(native.mc, "screen")
    assert native.code["ready"]() is True
    api.screen_name.assert_called_once_with()
    api.screen_name.return_value = "Chat"
    assert native.code["ready"]() is False


@pytest.mark.parametrize("reason", ["refused", "water", "menu", "damage", "world", "f8"])
def test_native_launch_does_not_boost_after_rejection_or_interruption(native_runtime, reason):
    native = native_runtime
    native.code["arm"]()
    native.state.grounded = False
    if reason == "refused":
        native.state.eligible = False
    elif reason == "water":
        native.state.eligible = False
    elif reason == "menu":
        api.screen_name.return_value = "menu"
    elif reason == "damage":
        native.state.health = 18
    elif reason == "world":
        native.mc.level = object()
    else:
        native.listeners["key"](NS(key=297, action=1))
    for _ in range(45):
        native.listeners["tick"](None)
    native.use.assert_not_called()
    native.code["stop"]()
    api.player_press_jump.assert_called_with(False)
    assert api.remove_event_listener.call_count == 2


@pytest.mark.parametrize("problem", ["explosive", "wrong_item", "grounded", "not_gliding"])
def test_native_boost_checks_actual_held_item_and_flight(native_runtime, problem):
    native = native_runtime
    native.state.flying = problem != "not_gliding"
    native.state.grounded = problem == "grounded"
    native.state.explosive = problem == "explosive"
    native.state.slot_is_rocket = problem != "wrong_item"
    assert native.code["burn"]() == 0
    native.use.assert_not_called()


def test_native_boost_honors_rocket_duration_and_game_rejection(native_runtime):
    native = native_runtime
    native.state.grounded, native.state.flying = False, True
    native.state.duration = 3
    assert native.code["burn"]() == pytest.approx(3.15)
    native.state.accepted = False
    assert native.code["burn"]() == 0


def test_native_surface_lookup_skips_unloaded_chunks(native_runtime):
    native = native_runtime
    native.level.hasChunk = lambda x, z: x >= 0 and z >= 0
    rows = native.code["surfaces"](0, 0, 4).split(";")
    assert len(rows) == 4
    assert all(int(row.split(",")[0]) >= 0 and int(row.split(",")[2]) >= 0 for row in rows)


def test_native_wrapper_releases_embedded_script_on_close(monkeypatch):
    script = MagicMock()
    script.get.side_effect = lambda name: {"status": 2.15}.get(name, Mock())
    monkeypatch.setitem(sys.modules, "java", NS(eval_pyjinn_script=lambda source: script))
    native = NativeFlightClass()
    assert native.status() == 2.15
    native.close()
    native.stop.assert_called_once()
    script.exit.assert_called_once()


@pytest.mark.parametrize(
    "position,velocity",
    [
        ((0, 120, 0), (0, 0, 1.4)),
        ((0, 180, 150), (0, -0.2, 1.4)),
        ((0, 70, 180), (0, -0.3, 1.5)),
        ((20, 80, 220), (1, -0.2, 1)),
        ((0, 100, 200), (0, -0.2, 1)),
        ((0, 68, 200), (0, -0.1, 0.1)),
    ],
)
@pytest.mark.parametrize("interval", [4, 10])
def test_landing_feedback_in_unboosted_flight_model(position, velocity, interval):
    """Model exercise only: no terrain, wind, effects, server or live client."""
    destination = common.Destination(0, 200, 64)
    for tick in range(1000):
        if tick % interval == 0:
            yaw, pitch = elytra.landing_angles(position, velocity, destination)
        velocity = elytra.glide_step(velocity, yaw, pitch)
        position = tuple(a + b for a, b in zip(position, velocity, strict=True))
        if position[1] <= 64:
            break
    else:
        pytest.fail("Landing model never touched down")
    assert destination.distance(position) < 3.5
    assert math.hypot(velocity[0], velocity[2]) < 0.55
    assert velocity[1] >= -0.5


def test_fuel_saving_glides_for_more_than_four_seconds_without_boost(game):
    with common.Session(game.client) as session:
        flight = elytra.Flight(session, common.Destination(1000, 0), 50)
        session.position, session.velocity = (0, 120, 0), (0, -0.15, 1.1)
        assert not flight.needs_boost(60)
        session.position = (0, 80, 0)
        assert flight.needs_boost(60)
        flight.climbing = True
        assert not flight.needs_boost(60)
        flight.climbing = False
        flight.boost_until = 61
        assert not flight.needs_boost(60)
        flight.boost_until = 0
        flight.landing = common.Destination(0, 0, 64)
        assert not flight.needs_boost(60)


def test_landing_search_accepts_five_by_five_and_searches_beyond_four_blocks():
    def blocks(positions):
        return [
            "minecraft:stone"
            if p[1] == 63 and 10 <= p[0] <= 14 and -2 <= p[2] <= 2
            else "minecraft:air"
            for p in positions
        ]

    api.getblocklist.side_effect = blocks
    assert elytra.landing_area(common.Destination(0, 0, 64), (0, 100, 0)) == common.Destination(
        12.5, 0.5, 64
    )
    assert len(api.getblocklist.call_args.args[0]) < 20_000


@pytest.mark.parametrize(
    "coordinates,expected",
    [
        (["~100", "~-20"], ["100.5", "-19.5"]),
        (["~100", "~", "~-20"], ["100.5", "64", "-19.5"]),
        (["12345678.25", "-12345678.5"], ["12345678.25", "-12345678.5"]),
    ],
)
def test_walking_handoff_uses_original_resolved_destination(
    game, monkeypatch, coordinates, expected
):
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]

    def landed(_):
        game.player.position = (40, 64, 30)

    monkeypatch.setattr(elytra.Flight, "fly", landed)
    walk = Mock()
    monkeypatch.setattr(elytra, "walk_main", walk)
    elytra.main(coordinates)
    walk.assert_called_once_with([*expected, "--eat-at", "14"])


def test_landing_waits_for_existing_rocket_to_finish(game):
    api.getblocklist.side_effect = flat_blocks
    with common.Session(game.client) as session:
        session.position = (0, 120, 0)
        game.player.position = session.position
        flight = elytra.Flight(session, common.Destination(100, 0), 50)
        flight.boost_until = game.clock.now + 1
        flight.begin_landing()
        assert game.clock.now >= flight.boost_until
        game.native.burn.assert_not_called()


@pytest.mark.parametrize(
    "args,expected",
    [
        (["1", "1"], common.Destination(1, 1)),
        (["1200", "67", "-500"], common.Destination(1200, -500, 67)),
        (["~100", "~-20"], common.Destination(110.5, -62.25)),
        (["~100", "~2", "~-20"], common.Destination(110.5, -62.25, 69)),
    ],
)
def test_axes_and_relative_coordinates_use_the_correct_origin(game, args, expected):
    game.player.position = (10.5, 67, -42.25)
    for flight in (False, True):
        assert common.arguments(args, flight=flight).destination == expected


def test_destination_display_labels_x_y_z_without_changing_values():
    assert common.Destination(1, 1).describe() == "X=1.000, Y=surface, Z=1.000"
    target = common.Destination(12345678.125, -7654321.25, 67)
    assert target.describe() == "X=12345678.125, Y=67.000, Z=-7654321.250"
    assert target.x == 12345678.125 and target.z == -7654321.25


def test_walking_handoff_waits_for_touchdown_snapshot_and_momentum_to_settle(game, monkeypatch):
    game.player.position, game.player.velocity = (1.7, 67.35, -3.7), (0, -0.15, 0.2)

    def sleep(seconds):
        game.clock.now += seconds
        if game.clock.now >= 0.2:
            game.player.position, game.player.velocity = (1.7, 67, -3.7), (0, 0, 0)

    monkeypatch.setattr(common.time, "sleep", sleep)
    with common.Session(game.client) as session:
        elytra.prepare_walk(session, common.Destination(1, 1))
    assert game.clock.now >= 0.5
    assert any("4.8 blocks left to X=1.000" in str(args) for args in api.echo.call_args_list)
    assert call(True) not in api.player_press_forward.call_args_list


def test_unsupported_touchdown_reports_actual_position_and_original_destination(game):
    game.player.position = (1.7, 67.5, -3.7)
    with common.Session(game.client) as session, pytest.raises(common.Stopped) as error:
        elytra.prepare_walk(session, common.Destination(1, 1))
    assert "Y=67.500" in str(error.value)
    assert "original destination: X=1.000, Y=surface, Z=1.000" in str(error.value)
    assert call(True) not in api.player_press_forward.call_args_list


def test_f8_during_touchdown_settling_stops_before_walking(game):
    def event(*args, **kwargs):
        if game.clock.now >= 0.1:
            return NS(key=297, action=1)
        raise queue.Empty

    api.EventQueue.return_value.get.side_effect = event
    with common.Session(game.client) as session, pytest.raises(common.Stopped, match="F8"):
        elytra.prepare_walk(session, common.Destination(1, 1))
    assert call(True) not in api.player_press_forward.call_args_list


def test_flight_handoff_reaches_original_coordinates_after_settling(game, monkeypatch):
    """Exercise the actual walker after the landing boundary, without flying."""
    game.player.position = (20, 67, -50)
    state = walking_simulation(game, monkeypatch)
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:stone" if p[1] <= 66 else "minecraft:air" for p in positions
    ]
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]
    original_sleep = common.time.sleep
    landed_at = []

    def landed(_):
        game.player.position, game.player.velocity = (1.7, 67.35, -3.7), (0, -0.15, 0.2)
        landed_at.append(game.clock.now)

    def sleep(seconds):
        original_sleep(seconds)
        if landed_at and game.clock.now - landed_at[0] >= 0.2:
            x, _, z = game.player.position
            game.player.position, game.player.velocity = (x, 67, z), (0, 0, 0)

    monkeypatch.setattr(elytra.Flight, "fly", landed)
    monkeypatch.setattr(common.time, "sleep", sleep)
    elytra.main(["1", "1"])
    assert common.Destination(1, 1).reached(game.player.position)
    assert call("Arrived at the walking destination.") in api.echo.call_args_list
    assert not state.forward


@pytest.mark.parametrize("destination", [(80, 37), (-65, 23), (17, -71), (-48, -19)])
def test_arbitrary_directions_do_not_zigzag_back_to_cell_centers(game, monkeypatch, destination):
    state = walking_simulation(game, monkeypatch, delayed_scans=True)
    travel.main([str(destination[0]), str(destination[1])])
    assert common.Destination(*destination).reached(game.player.position)
    assert [held for held, _ in state.transitions].count(True) == 1
    # Every aim advances along the requested open-world direction.
    assert all(dx * destination[0] + dz * destination[1] > 0 for dx, dz in state.looks)
    assert state.distance < 1.05 * math.hypot(destination[0] - 0.5, destination[1] - 0.5)


def test_distant_goal_uses_its_bearing_instead_of_the_scan_corner():
    path = travel.plan(world(radius=12), (0, 64, 0), common.Destination(1000, 500))
    x, _, z = path[-1]
    assert abs(x * 0.5 - z) / math.hypot(1, 0.5) < 1
    assert x > z > 0


@pytest.mark.parametrize(
    "origin,goal", [((1.95, 64, 1.95), (1, 1)), ((-0.05, 64, -0.05), (-1, -1))]
)
def test_final_approach_inside_the_destination_block_still_finishes(
    game, monkeypatch, origin, goal
):
    game.player.position = origin
    state = walking_simulation(game, monkeypatch)
    travel.main([str(goal[0]), str(goal[1])])
    assert common.Destination(*goal).reached(game.player.position)
    assert not state.forward


def test_body_width_corridor_rejects_corner_clipping_and_side_holes():
    terrain = world({(1, 64, 0): "minecraft:stone"})
    assert not terrain.corridor((0.5, 64, 0.5), (1.5, 64, 1.5), 64)
    terrain = world({(1, 63, 0): "minecraft:air"})
    assert not terrain.corridor((0.9, 64, 0.5), (0.9, 64, 4.5), 64)
    assert terrain.corridor((0.5, 64, 0.5), (0.5, 64, 4.5), 64)


@pytest.mark.parametrize("kind", ["wall", "hole"])
@pytest.mark.parametrize("inertia", [False, True])
def test_walk_detours_with_full_body_clearance(game, monkeypatch, kind, inertia):
    # Independent axis-aligned geometry: a 0.6-wide body must never intersect
    # the rectangle, even between position updates and during delayed scans.
    obstacle = (1, 3, 3, 8)  # x min/max, z min/max; target is beyond it.
    game.player.position = (1.5, 64, 0.5)
    state = walking_simulation(game, monkeypatch)
    original_sleep = common.time.sleep
    velocity = [0.0, 0.0]

    def blocks(positions):
        output = []
        for x, y, z in positions:
            inside = obstacle[0] <= x < obstacle[1] and obstacle[2] <= z < obstacle[3]
            output.append(
                "minecraft:air"
                if kind == "hole" and inside
                else "minecraft:stone"
                if y <= 63 or inside and y <= 65
                else "minecraft:air"
            )
        return output

    api.getblocklist.side_effect = blocks

    def sleep(seconds):
        remaining = seconds
        while remaining > 0:
            delta = min(0.025, remaining)
            before = game.player.position
            original_sleep(delta)
            if inertia:
                speed = (1.3 if state.sneak else 4.3) if state.forward else 0
                fraction = 1 - math.exp(-delta / 0.08)
                for index in (0, 1):
                    velocity[index] += (state.direction[index] * speed - velocity[index]) * fraction
                game.player.position = (
                    before[0] + velocity[0] * delta,
                    64,
                    before[2] + velocity[1] * delta,
                )
            remaining -= delta
            x, _, z = game.player.position
            overlaps = (
                x + 0.3 > obstacle[0]
                and x - 0.3 < obstacle[1]
                and z + 0.3 > obstacle[2]
                and z - 0.3 < obstacle[3]
            )
            assert not overlaps, "Body entered an obstacle or unsupported floor"

    monkeypatch.setattr(common.time, "sleep", sleep)
    travel.main(["1.5", "13"])
    assert common.Destination(1.5, 13).reached(game.player.position)
    assert not state.forward


def test_native_walk_lease_brakes_and_rejects_stale_timeouts(game):
    timers = []
    api.add_event_listener.side_effect = lambda *args: 99
    api.set_timeout.side_effect = lambda callback, millis, *args: (
        timers.append((callback, millis, args)) or len(timers)
    )
    code = {"JavaInt": JavaInt32, "JavaClass": lambda name: NS(sqrt=math.sqrt)}
    exec(compile(travel.NATIVE_WALK_LEASE, "<walk-lease>", "exec"), code)  # noqa: S102
    assert code["drive"](600, False)
    first = timers[-1]
    assert type(first[1]) is JavaInt32
    assert code["drive"](700, False)
    first[0](*first[2])
    assert api.player_press_forward.call_args_list == [call(True)]
    last = timers[-1]
    last[0](*last[2])
    api.player_press_forward.assert_called_with(False)
    assert code["drive"](600, True)
    api.player_press_jump.reset_mock()
    last = timers[-1]
    last[0](*last[2])
    api.player_press_jump.assert_not_called()  # An expired lease must not sink a swimmer.
    code["key"](NS(key=297, action=1))
    assert code["drive"](600, False) == -1
    api.player_press_jump.assert_called_with(False)


def test_native_walk_lease_menu_abort_and_cleanup(game):
    api.add_event_listener.side_effect = lambda *args: 99
    api.set_timeout.return_value = 123
    code = {"JavaInt": JavaInt32, "JavaClass": lambda name: NS(sqrt=math.sqrt)}
    exec(compile(travel.NATIVE_WALK_LEASE, "<walk-lease>", "exec"), code)  # noqa: S102
    code["drive"](600, False)
    api.screen_name.return_value = "Chat"
    code["tick"](None)
    assert code["drive"](600, False) == -1
    code["close"]()
    api.player_press_forward.assert_called_with(False)


def test_native_water_runway_never_crouches_or_cancels_floating(game):
    api.add_event_listener.side_effect = lambda *args: 99
    api.set_timeout.return_value = 123
    code = {"JavaInt": JavaInt32, "JavaClass": lambda name: NS(sqrt=math.sqrt)}
    exec(compile(travel.NATIVE_WALK_LEASE, "<walk-lease>", "exec"), code)  # noqa: S102
    code["drive"](500, True, True, 0.5, 0.5, 0.5)
    code["drive"](500, True, True, 0.5, 0.5, 0.5)
    api.player_press_sneak.assert_called_with(False)
    assert call(True) not in api.player_press_sneak.call_args_list
    api.player_press_jump.assert_not_called()


def test_walk_lease_wrapper_uses_a_bounded_checked_distance(monkeypatch):
    script = MagicMock()
    drive = Mock(return_value=True)
    script.get.side_effect = lambda name: drive if name == "drive" else Mock()
    monkeypatch.setitem(sys.modules, "java", NS(eval_pyjinn_script=lambda source: script))
    lease = WalkLeaseClass()
    lease.drive(5)
    assert 500 <= drive.call_args.args[0] <= 700
    drive.return_value = -1
    with pytest.raises(common.Stopped, match="F8"):
        lease.drive(5)
    lease.close()
    script.exit.assert_called_once()


@pytest.mark.parametrize("rise", [1, -1])
def test_elevation_step_uses_one_forward_hold_and_never_aims_back(game, monkeypatch, rise):
    start_y = 64 if rise > 0 else 65
    end_y = start_y + rise
    game.player.position = (0.5, start_y, 0.5)
    state = walking_simulation(game, monkeypatch)
    physics = NS(vy=0.0, grounded=True)
    game.client.grounded.side_effect = lambda: physics.grounded
    advance = common.time.sleep
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:stone" if y < (start_y if z < 1 else end_y) else "minecraft:air"
        for x, y, z in positions
    ]

    def jump(pressed):
        if pressed and physics.grounded:
            physics.vy, physics.grounded = 8.4, False

    api.player_press_jump.side_effect = jump

    def sleep(seconds):
        remaining = seconds
        while remaining > 0:
            delta = min(0.01, remaining)
            previous_y = game.player.position[1]
            advance(delta)
            x, _, z = game.player.position
            if rise > 0 and previous_y < end_y and z + 0.3 > 1:
                z = 0.7  # Solid riser blocks horizontal motion until the jump clears it.
            floor = start_y if z + 0.29 < 1 else end_y
            physics.vy -= 32 * delta
            y = previous_y + physics.vy * delta
            if y <= floor and physics.vy <= 0:
                y, physics.vy, physics.grounded = floor, 0, True
            else:
                physics.grounded = False
            game.player.position = (x, y, z)
            remaining -= delta

    monkeypatch.setattr(common.time, "sleep", sleep)
    with common.Session(game.client) as session:
        walker = travel.Walker(session)
        assert travel.move(
            session,
            (0, start_y, 0),
            (0, end_y, 1),
            walker=walker,
            continuation=[(0, end_y, 2), (0, end_y, 3)],
        )
        assert walker.walking
        walker.close()
    assert [held for held, _ in state.transitions].count(True) == 1
    assert all(dz > 0 for _, dz in state.looks)
    assert api.player_press_jump.call_args_list.count(call(True)) == (1 if rise > 0 else 0)


def test_rejected_jump_stops_quickly_without_repeated_space_presses(game):
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:stone" if y < (64 if z < 1 else 65) else "minecraft:air" for x, y, z in positions
    ]
    with common.Session(game.client) as session:
        assert not travel.move(session, (0, 64, 0), (0, 65, 1))
    assert game.clock.now < 2
    assert api.player_press_jump.call_args_list.count(call(True)) == 1


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
        in_water=Mock(return_value=False),
        underwater=Mock(return_value=False),
    )
    monkeypatch.setattr(travel, "Client", lambda: client)
    monkeypatch.setattr(elytra, "Client", lambda: client)
    native = NS(
        arm=Mock(),
        stop=Mock(),
        close=Mock(),
        burn=Mock(return_value=2.15),
        status=Mock(return_value=-1),
        surfaces=Mock(
            side_effect=lambda x, z, r: ";".join(
                f"{x + dx},64,{z + dz}" for dx in range(-r, r + 1, 4) for dz in range(-r, r + 1, 4)
            )
        ),
    )
    monkeypatch.setattr(elytra, "NativeFlight", lambda: native)
    leases = []

    class FakeWalkLease:
        def __init__(self):
            self.active = False
            self.deadline = math.inf
            self.wet = False
            leases.append(self)

        def drive(self, distance, wet=False, *, origin=None):
            api.player_press_sneak(distance < 1.2)
            if not self.active:
                api.player_press_forward(True)
                self.active = True
            self.deadline = clock.now + travel.walk_budget(distance) / 1000
            self.wet = wet
            return True

        def stop(self):
            if self.active:
                api.player_press_forward(False)
                self.active = False

        def close(self):
            self.stop()

    monkeypatch.setattr(travel, "WalkLease", FakeWalkLease)
    return NS(player=player, clock=clock, client=client, native=native, leases=leases)


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


def test_astar_avoids_lava_and_cliffs():
    terrain = world(
        {
            (1, 63, 0): "minecraft:lava",
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
    assert path[-1][0] == 7  # Keep a border for body width and the next safety check.
    assert len(path) <= 16


def test_no_route_is_reported_without_movement():
    terrain = world(
        {
            (x, y, z): "minecraft:stone"
            for x, z in ((1, 0), (-1, 0), (0, 1), (0, -1))
            for y in (64, 65, 66)
        }
    )
    with pytest.raises(common.Stopped, match="No walking/swimming route"):
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
    game.native.burn.assert_called_once()
    assert call(True) not in api.player_press_use.call_args_list


def test_takeoff_checks_overhead_before_any_jump(game):
    game.client.flying.return_value = False
    api.getblocklist.side_effect = lambda positions: ["minecraft:stone"] * len(positions)
    with common.Session(game.client) as session, pytest.raises(common.Stopped, match="clear space"):
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    assert call(True) not in api.player_press_jump.call_args_list


def test_failed_elytra_open_does_not_fire_a_rocket(game):
    game.client.flying.return_value = False
    api.getblocklist.side_effect = flat_blocks
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]
    with (
        common.Session(game.client) as session,
        pytest.raises(common.Stopped, match="Jump did not leave"),
    ):
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    assert call(True) not in api.player_press_use.call_args_list
    api.player_press_jump.assert_called_with(False)


def test_cruise_uses_shallow_glide_and_landing_accounts_for_velocity():
    target = common.Destination(0, 100, 64)
    assert elytra.flight_angles((0, 64, 0), (0, 0, 1), target, 200) == (0, -2)
    fast = elytra.flight_angles((0, 68, 95), (0, -0.3, 1), target, 120, True)
    slow = elytra.flight_angles((0, 68, 95), (0, -0.1, 0.1), target, 120, True)
    assert fast != slow


def test_landing_area_accepts_a_clear_flat_pad():
    api.getblocklist.side_effect = flat_blocks
    target = elytra.landing_area(common.Destination(0, 0, 64), (0, 100, 0))
    assert target == common.Destination(0.5, 0.5, 64)


def test_landing_area_rejects_liquid_or_holes():
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:water" if p[1] == 63 else "minecraft:air" for p in positions
    ]
    with pytest.raises(common.Stopped, match="No dry"):
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
        isInWater=lambda: False,
        isUnderWater=lambda: False,
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
    if shortage == "fuel":
        inventory = api.player_inventory.return_value
        api.player_inventory.side_effect = [inventory, [], [], [], [], []]
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
            if y == 64:
                game.player.velocity = (0, 0, 0)
        else:
            z += seconds * 30
        game.player.position = (x, y, z)

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
        sneak=False,
        distance=0.0,
    )

    def advance(seconds):
        end = game.clock.now + max(seconds, 0.001)
        while game.clock.now < end:
            deadline = min(
                (lease.deadline for lease in game.leases if lease.active), default=math.inf
            )
            elapsed = max(0, min(end, deadline) - game.clock.now)
            if state.forward:
                x, y, z = game.player.position
                dx, dz = state.direction
                speed = 1.3 if state.sneak else 4.3
                game.player.position = (x + dx * speed * elapsed, y, z + dz * speed * elapsed)
                state.distance += speed * elapsed
            game.clock.now += elapsed
            for lease in game.leases:
                if lease.active and game.clock.now >= lease.deadline:
                    lease.stop()
                    if not lease.wet:
                        api.player_press_jump(False)
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
    api.player_press_sneak.side_effect = lambda held: setattr(state, "sneak", held)
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
            "minecraft:lava"
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
        {(1, 63, 0): "minecraft:lava"},
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


def test_launch_preloads_rocket_and_always_restores_slot(game):
    api.getblocklist.side_effect = flat_blocks
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]
    game.client.flying.return_value = False
    game.native.status.return_value = 2.15
    with common.Session(game.client) as session:
        flight = elytra.Flight(session, common.Destination(100, 0), 50)
        flight.takeoff()
        assert flight.rockets_used == 1
        assert flight.boost_until > game.clock.now
    game.native.arm.assert_called_once()
    game.native.stop.assert_called_once()
    assert api.player_inventory_select_slot.call_args_list == [call(1), call(4)]
    game.client.request_glide.assert_not_called()


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


def test_refused_native_launch_returns_control_and_restores_slot(game):
    api.getblocklist.side_effect = flat_blocks
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]
    game.client.flying.return_value = False
    game.client.grounded.return_value = False
    with common.Session(game.client) as session, pytest.raises(common.Stopped, match="refused"):
        elytra.Flight(session, common.Destination(100, 0), 50).takeoff()
    game.native.stop.assert_called_once()
    assert api.player_inventory_select_slot.call_args_list[-1] == call(4)


def test_f8_during_jump_releases_space_and_does_not_boost(game):
    api.getblocklist.side_effect = flat_blocks
    api.player_inventory.return_value = [NS(item="minecraft:firework_rocket", count=64, slot=1)]
    game.client.flying.return_value = False

    game.native.status.return_value = 0

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


def river_blocks(positions):
    return [
        "minecraft:water[level=0]"
        if 2 <= p[2] <= 12 and p[1] <= 63
        else "minecraft:stone"
        if p[1] <= 63
        else "minecraft:air"
        for p in positions
    ]


def test_pathfinder_crosses_a_river_without_a_solid_riverbed():
    positions = [(x, y, z) for x in range(-4, 5) for y in range(58, 68) for z in range(17)]
    terrain = travel.Terrain(dict(zip(positions, river_blocks(positions), strict=True)))
    path = travel.plan(terrain, (0, 64, 0), common.Destination(0, 16, 64))
    assert path[-1] == (0, 64, 16)
    assert any(terrain.swimmable(p) for p in path)
    assert all(terrain.traversable(p) for p in path)
    assert not terrain.standable((0, 64, 5)), (
        "A swimming cell must not become an Elytra landing pad"
    )


@pytest.mark.parametrize(
    "state", ["minecraft:lava", "minecraft:bubble_column", "minecraft:water[level=8]"]
)
def test_swimming_does_not_allow_lava_bubble_columns_or_waterfalls(state):
    terrain = world({(1, 63, 0): state})
    assert not terrain.swimmable((1, 64, 0))
    assert not terrain.edge((0, 64, 0), (1, 64, 0))


def test_water_surface_projection_accepts_bobbing_feet_and_rejects_an_ice_roof():
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:water" if p[1] <= 63 else "minecraft:air" for p in positions
    ]
    assert travel.navigation_cell((0.5, 63.55, 0.5), afloat=True) == (0, 64, 0)
    assert travel.navigation_cell((0.5, 64.1, 0.5), afloat=True) == (0, 64, 0)
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:water"
        if p[1] <= 63
        else "minecraft:packed_ice"
        if p[1] == 64
        else "minecraft:air"
        for p in positions
    ]
    with pytest.raises(common.Stopped, match="No open water surface"):
        travel.navigation_cell((0.5, 63.55, 0.5), afloat=True)


def test_surface_arrival_tolerates_float_height_but_not_a_dry_bank_or_submersion():
    target = common.Destination(0, 0, 64)
    api.getblocklist.return_value = ["minecraft:water", "minecraft:air", "minecraft:air"]
    assert travel.arrived(target, (0.5, 63.55, 0.5), afloat=True)
    assert not travel.arrived(target, (0.5, 63.55, 0.5), afloat=True, submerged=True)
    api.getblocklist.return_value = ["minecraft:stone", "minecraft:air", "minecraft:air"]
    assert not travel.arrived(target, (0.5, 63.55, 0.5), afloat=True)


@pytest.mark.parametrize("hunger", [False, True])
def test_traveler_swims_a_river_eats_afloat_and_resumes_walking(game, monkeypatch, hunger):
    """Approximate water movement to verify controller transitions, not fluid physics."""
    state = walking_simulation(game, monkeypatch, hunger=hunger)
    original_sleep = common.time.sleep
    state.jump = False
    wet_samples = []
    api.player_press_jump.side_effect = lambda held: setattr(state, "jump", held)
    api.getblocklist.side_effect = river_blocks

    def in_water():
        return 2 <= math.floor(game.player.position[2]) <= 12

    game.client.in_water.side_effect = in_water
    game.client.grounded.side_effect = lambda: not in_water()
    game.client.underwater.side_effect = lambda: in_water() and game.player.position[1] + 1.62 < 64

    def swim(seconds):
        old = game.player.position
        was_wet = in_water()
        original_sleep(seconds)
        x, _, z = game.player.position
        if was_wet:
            x = old[0] + (x - old[0]) * 2 / 4.3
            z = old[2] + (z - old[2]) * 2 / 4.3
        if 2 <= math.floor(z) <= 12:
            assert state.jump, "Hold jump in water, including when eating"
            wet_samples.append((state.use, state.jump))
            game.player.position = (x, 63.55, z)
        else:
            game.player.position = (x, 64, z)

    monkeypatch.setattr(common.time, "sleep", swim)
    if hunger:
        api.player_inventory.return_value = [NS(item="minecraft:cooked_beef", count=3, slot=0)]
    travel.main(["0", "64", "20"])
    assert common.Destination(0, 20, 64).reached(game.player.position)
    assert wet_samples
    assert [held for held, _ in state.transitions].count(True) == (2 if hunger else 1)
    assert any(eating for eating, _ in wet_samples) is hunger
    assert not state.jump
    assert not state.forward


def test_starting_underwater_surfaces_before_eating_or_moving_forward(game, monkeypatch):
    game.player.position = (0.5, 60, 0.5)
    game.client.in_water.return_value = True
    game.client.grounded.return_value = False
    game.client.underwater.side_effect = lambda: game.player.position[1] + 1.62 < 64
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:water" if p[1] <= 63 else "minecraft:air" for p in positions
    ]

    def ascend(seconds):
        game.clock.now += seconds
        assert api.player_press_jump.call_args == call(True)
        assert call(True) not in api.player_press_forward.call_args_list
        assert call(True) not in api.player_press_use.call_args_list
        x, y, z = game.player.position
        game.player.position = x, min(63.55, y + seconds * 2), z

    monkeypatch.setattr(common.time, "sleep", ascend)
    # Already at the X/Z destination, but must regain breathable air first.
    travel.main(["0", "0"])
    assert not game.client.underwater()
    api.player_press_jump.assert_called_with(False)


def test_water_check_is_read_only(game):
    game.player.position = (0.5, 63.55, 4.5)
    game.client.in_water.return_value = True
    game.client.grounded.return_value = False
    api.getblocklist.side_effect = river_blocks
    travel.main(["0", "64", "16", "--check"])
    api.player_press_jump.assert_not_called()
    api.player_press_forward.assert_not_called()
    api.player_press_use.assert_not_called()


@pytest.mark.parametrize("position", [(0.05, 64, 0.05), (0.95, 64, 0.95)])
def test_walking_can_start_away_from_the_center_of_a_block(game, monkeypatch, position):
    game.player.position = position
    state = walking_simulation(game, monkeypatch, delayed_scans=True)
    travel.main(["0", "64", "40"])
    assert common.Destination(0, 40, 64).reached(game.player.position)
    assert [held for held, _ in state.transitions].count(True) == 1


def test_slow_position_updates_resynchronize_to_later_route_cells(game, monkeypatch):
    state = walking_simulation(game, monkeypatch)
    advance = common.time.sleep
    state.delayed_once = False

    def slow_blocks(positions):
        if state.forward and not state.delayed_once and game.clock.now >= 0.2:
            state.delayed_once = True
            advance(0.75)  # Native lease brakes during the stalled game-bridge call.
        return flat_blocks(positions)

    api.getblocklist.side_effect = slow_blocks
    travel.main(["0", "64", "40"])
    assert state.delayed_once
    assert common.Destination(0, 40, 64).reached(game.player.position)
    assert [held for held, _ in state.transitions].count(True) == 2
    assert all(dz > 0 for _, dz in state.looks)
    assert all(dz > 0 for _, dz in state.looks)


def test_swimming_can_approach_a_one_block_higher_bank(game, monkeypatch):
    game.player.position = (0.5, 63.55, 0.5)
    game.client.in_water.side_effect = lambda: game.player.position[1] < 65
    game.client.grounded.side_effect = lambda: game.player.position[1] >= 65
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:water"
        if p[0] == 0 and p[1] <= 63
        else "minecraft:stone"
        if p[0] != 0 and p[1] <= 64
        else "minecraft:air"
        for p in positions
    ]

    def reach_bank(seconds):
        game.clock.now += 0.2
        assert api.player_press_jump.call_args == call(True)
        game.player.position = (1.5, 65, 0.5)

    monkeypatch.setattr(common.time, "sleep", reach_bank)
    with common.Session(game.client) as session:
        walker = travel.Walker(session)
        completed, blocked = walker.follow((0, 64, 0), [(1, 65, 0)])
        assert completed == [(1, 65, 0)]
        assert not blocked
        assert not walker.floating


def test_surfacing_raises_feet_high_enough_even_after_the_eyes_reach_air(game, monkeypatch):
    game.player.position = (0.5, 62.7, 0.5)
    game.client.in_water.return_value = True
    game.client.grounded.return_value = False
    game.client.underwater.return_value = False
    api.getblocklist.side_effect = lambda positions: [
        "minecraft:water" if p[1] <= 63 else "minecraft:air" for p in positions
    ]

    def rise(seconds):
        game.clock.now += seconds
        x, y, z = game.player.position
        game.player.position = (x, y + seconds * 2, z)

    monkeypatch.setattr(common.time, "sleep", rise)
    with common.Session(game.client) as session:
        walker = travel.Walker(session)
        walker.surface()
        assert session.position[1] >= 63.1
        walker.stop()
