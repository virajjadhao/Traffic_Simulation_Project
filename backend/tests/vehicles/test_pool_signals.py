from src.controllers.fixed_time_signal import FixedTimeSignalController
from src.core.enums import Direction, TurnIntent
from src.roads.network import RoadNetwork
from src.vehicles.idm import IntelligentDriverModel
from src.vehicles.pool import VehiclePool
from src.vehicles.spawner import VehicleSpawner
from src.vehicles.vehicle import Vehicle


def _make_network() -> RoadNetwork:
    net = RoadNetwork()
    net.setup_default_intersection(
        approach_length=100.0,
        lane_width=3.5,
        lanes_per_approach=1,
    )
    return net


def test_pool_signal_colors_integration() -> None:
    """Verify that vehicles decelerate under Yellow/Red and accelerate under Green."""
    network = _make_network()
    # Mock spawner
    spawner = VehicleSpawner(network, arrival_rate=1.0, total_vehicles=1)
    spawner.try_spawn = lambda t: None  # type: ignore[assignment]
    idm = IntelligentDriverModel(max_acceleration=2.0, comfort_deceleration=3.0)

    # Initialize controller: 10s green, 2s yellow, 1s all_red
    ctrl = FixedTimeSignalController(green_time=10.0, yellow_time=2.0, all_red_time=1.0)
    pool = VehiclePool(spawner, idm)

    # Create vehicle starting at 75m in North incoming approach (length 96.5m)
    # Moving straight towards the intersection
    route = network.generate_route(Direction.NORTH, 0, TurnIntent.STRAIGHT)
    vehicle = Vehicle(
        "v_north",
        length=4.0,
        width=2.0,
        desired_speed=13.89,
        route=route,
        start_position=75.0,
        initial_speed=10.0,
    )
    pool._active.append(vehicle)

    # 1. Test GREEN phase (initially ns_green)
    signals = {
        Direction(sig["direction"]): sig["color"] for sig in ctrl.get_signals_state()
    }
    pool.set_traffic_signals(signals)
    pool.update(dt=0.1, elapsed_time=0.1)

    # Under Green phase, the vehicle has no obstacle and should continue
    assert vehicle.acceleration >= 0.0

    # 2. Transition controller to ns_yellow (after 10.0 seconds)
    ctrl.update(10.0, [])
    assert ctrl.current_phase == "ns_yellow"
    signals = {
        Direction(sig["direction"]): sig["color"] for sig in ctrl.get_signals_state()
    }
    pool.set_traffic_signals(signals)
    pool.update(dt=0.1, elapsed_time=10.2)

    # Under Yellow phase, the vehicle must yield at the stop line and decelerate
    assert vehicle.acceleration < 0.0

    # 3. Transition controller to all_red (after 2.0 more seconds)
    ctrl.update(2.0, [])
    assert ctrl.current_phase == "all_red"
    signals = {
        Direction(sig["direction"]): sig["color"] for sig in ctrl.get_signals_state()
    }
    pool.set_traffic_signals(signals)
    pool.update(dt=0.1, elapsed_time=12.3)

    # Under Red phase, the vehicle continues to decelerate
    assert vehicle.acceleration < 0.0
